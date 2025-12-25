from __future__ import annotations

import hashlib
import json
import os
import tempfile
from typing import List, Dict
from tifftopdf.models import OrchestratorConfig, ResumeState, GroupStatus

import os
from typing import List, Tuple, Dict

def _list_immediate_subdirs(root: str) -> List[Tuple[str, str]]:
    out: List[Tuple[str, str]] = []
    with os.scandir(root) as it:
        for e in it:
            if e.is_dir():
                out.append((e.name, e.path))
    return out

def resolve_preferred_batches(input_root: str) -> List[Tuple[str, str]]:
    """
    Descobre subpastas imediatas de `input_root` e aplica a política:
      - Para cada 'base' (texto até o primeiro '_'):
        - Se houver cópias base_* → escolhe a cópia com mtime mais recente.
        - Caso contrário → escolhe o original (base), se existir.
        - Se só houver cópias (sem original) → escolhe a cópia mais recente.
    Retorna lista de (nome_escolhido, caminho_escolhido), ordenada pelo nome.
    """
    if not os.path.isdir(input_root):
        raise ValueError(f"input_root not found or not a directory: {input_root}")

    entries = _list_immediate_subdirs(input_root)  # [(name, path)]
    if not entries:
        return []

    # Agrupar por 'base'
    groups: Dict[str, Dict[str, list]] = {}
    for name, path in entries:
        if "_" in name:
            base = name.split("_", 1)[0]
            is_copy = True
        else:
            base = name
            is_copy = False

        info = {
            "name": name,
            "path": path,
            "mtime": os.path.getmtime(path),
            "is_copy": is_copy,
        }
        g = groups.setdefault(base, {"originals": [], "copies": []})
        (g["copies"] if is_copy else g["originals"]).append(info)

    chosen: List[Tuple[str, str]] = []
    for base, g in groups.items():
        if g["copies"]:
            # escolhe a cópia mais recente
            best = max(g["copies"], key=lambda x: x["mtime"])
            chosen.append((best["name"], best["path"]))
        else:
            # sem cópias → usa original (se existir)
            if g["originals"]:
                # se houver mais de um diretório chamado exatamente 'base' (caso bizarro),
                # escolha o mais recente:
                best = max(g["originals"], key=lambda x: x["mtime"])
                chosen.append((best["name"], best["path"]))
            # senão: não há nem original nem cópia (grupo vazio) → ignora

    return sorted(chosen, key=lambda x: x[0])


def _ensure_output_roots(cfg: OrchestratorConfig) -> tuple[str, str]:
    pdf_root = os.path.join(cfg.output_root, cfg.pdf_subdir_name)
    
    if cfg.metadata_root:
        meta_root = cfg.metadata_root
    else:
        meta_root = os.path.join(cfg.output_root, cfg.meta_subdir_name)
        
    os.makedirs(pdf_root, exist_ok=True)
    os.makedirs(meta_root, exist_ok=True)
    return pdf_root, meta_root


def _resolve_batches(cfg: OrchestratorConfig) -> List[Tuple[str, str]]:
    """
    Returns list of (batch_name, batch_path).
    If none found and allow_root_as_single_batch=True, treat input_root as one batch.
    """
    entries: List[Tuple[str, str]] = []
    with os.scandir(cfg.input_root) as it:
        for e in it:
            if e.is_dir():
                entries.append((e.name, e.path))
    if not entries and cfg.allow_root_as_single_batch:
        name = os.path.basename(os.path.normpath(cfg.input_root)) or "root"
        return [(name, cfg.input_root)]
    return sorted(entries, key=lambda x: x[0])


def _assert_output_outside_input(input_root: str, output_root: str) -> None:
    inp = os.path.realpath(input_root)
    out = os.path.realpath(output_root)


def fingerprint_group(files: List[str]) -> str:
    """
    Hash determinístico baseado em (path, mtime) de cada ficheiro.
    Garante que se as fontes mudarem, o fingerprint muda.
    """
    h = hashlib.sha1()
    for p in files:
        try:
            st = os.stat(p)
            h.update(p.encode("utf-8"))
            h.update(str(int(st.st_mtime)).encode("utf-8"))
            h.update(str(int(st.st_size)).encode("utf-8"))
        except FileNotFoundError:
            # se um ficheiro sumiu, incluímos mesmo assim o path
            h.update(p.encode("utf-8"))
            h.update(b"missing")
    return h.hexdigest()

def get_state_path(meta_root: str, filename: str) -> str:
    os.makedirs(meta_root, exist_ok=True)
    return os.path.join(meta_root, filename)

def load_state(state_path: str) -> ResumeState:
    if not os.path.isfile(state_path):
        return ResumeState()
    with open(state_path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    groups: Dict[str, GroupStatus] = {}
    for k, v in raw.get("groups", {}).items():
        groups[k] = GroupStatus(
            success=bool(v.get("success", False)),
            output_pdf=v["output_pdf"],
            input_files=list(v.get("input_files", [])),
            fingerprint=v.get("fingerprint", ""),
            finished_at=float(v.get("finished_at", 0.0)),
        )
    return ResumeState(groups=groups)

def save_state(state_path: str, state: ResumeState) -> None:
    tmp = state_path + ".tmp"
    payload = {
        "groups": {
            k: {
                "success": v.success,
                "output_pdf": v.output_pdf,
                "input_files": v.input_files,
                "fingerprint": v.fingerprint,
                "finished_at": v.finished_at,
            } for k, v in state.groups.items()
        }
    }
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=True)
    os.replace(tmp, state_path)  # atómico no mesmo filesystem

def mark_done(state: ResumeState, batch_name: str, group_id: str,
              output_pdf: str, files: List[str], fingerprint: str) -> None:
    key = f"{batch_name}:{group_id}"
    state.groups[key] = GroupStatus(
        success=True,
        output_pdf=output_pdf,
        input_files=list(files),
        fingerprint=fingerprint,
        finished_at=float(__import__("time").time()),
    )

def atomic_write_pdf(final_path: str, writer_func) -> None:
    """
    Escreve PDF de forma atómica: writer_func(tmp_path) -> rename(tmp, final).
    'writer_func' deve gerar o PDF em tmp_path.
    """
    d = os.path.dirname(final_path) or "."
    os.makedirs(d, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=d, delete=False, suffix=".tmp") as tmp:
        tmp_path = tmp.name
    try:
        writer_func(tmp_path)
        os.chmod(tmp_path, 0o666) 
        os.replace(tmp_path, final_path)
    except Exception:
        # limpeza em caso de falha
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        finally:
            raise
