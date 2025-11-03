# -*- coding: utf-8 -*-
import os, sys, re, json, requests
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, filedialog
from tkinter import font as tkfont

# ---- Drag & Drop (opcional) ----
try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    DND_AVAILABLE = True
except Exception:
    DND_AVAILABLE = False

import random
from datetime import datetime

# -------------------------------
# Frases aleatórias pro título
# -------------------------------
APP_TITLES = [
    "Mano Jarvis — já resolvo essas parada aí",
    "Jarvis Malandro — deixa comigo que eu arrumo",
    "Ô loco bicho, é o Jarvis arrumando seus arquivos!",
    "Jarvis — transformando txt véio em json bonitão",
    "Mano Jarvis — JSON no grau, CSV na mão",
    "Jarvis raiz — sem bug, só gambi",
    "Jarvis — clipa esse CSV e vai pro abraço",
    "Jarvis — hoje é dia de resolver treta de arquivo",
    "Jarvis — mais rápido que CTRL+C + CTRL+V",
    "Jarvis — eu sou inevitável... e formatador também",
    "Jarvis — os txt pira, os json chora",
]
APP_TITLE = random.choice(APP_TITLES)

def resource_path(rel_path: str) -> str:
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, rel_path)
    return os.path.join(os.path.abspath("."), rel_path)

# -------------------------------
# Conversão JSON → CSV (módulo existente)
# -------------------------------
FIELD_LABELS = {
    "Name": "Nome", "Number": "Número",
    "ShortSleeve": "Manga Curta", "LongSleeve": "Manga Longa",
    "Short": "Short", "Pants": "Calça",
    "Tanktop": "Regata", "Vest": "Colete",
    "Nickname": "Apelido", "BloodType": "Tipo Sanguíneo",
}
FIELD_ORDER = ["Name","Number","ShortSleeve","LongSleeve","Short","Pants","Tanktop","Vest","Nickname","BloodType"]
MANDATORY_FIELDS = {"Name","Number"}

def normalize_str(x):
    if x is None:
        return ""
    return str(x).replace("\r","").replace("\n"," ").strip()

def decide_effective_fields(orders):
    present = set()
    for entry in orders:
        for key in FIELD_ORDER:
            if key in MANDATORY_FIELDS:
                continue
            if normalize_str(entry.get(key,"")) != "":
                present.add(key)
    return [k for k in FIELD_ORDER if (k in MANDATORY_FIELDS) or (k in present)]

def format_lines(data):
    orders = data.get("orders", [])
    if not isinstance(orders, list):
        raise ValueError("Campo 'orders' inválido (não é lista).")
    eff = decide_effective_fields(orders)

    lines = []
    for e in orders:
        row_values = [normalize_str(e.get(k,"")) for k in eff]

        expanded_rows = []
        for idx, val in enumerate(row_values):
            m = re.match(r"^(\d+)-(.+)$", val)
            if m:
                qtd = int(m.group(1))
                base = m.group(2)
                for _ in range(qtd):
                    new_row = row_values.copy()
                    new_row[idx] = base
                    expanded_rows.append(",".join(new_row))
                break
        else:
            expanded_rows.append(",".join(row_values))

        lines.extend(expanded_rows)
    return lines, eff

def copy_to_clipboard(root, text):
    root.clipboard_clear()
    root.clipboard_append(text)
    root.update()

def do_convert_json_data(root, data, origem, status_widget=None):
    lines, fields = format_lines(data)
    out = "\n".join(lines)
    copy_to_clipboard(root, out)
    msg = [
        f"Origem: {origem}",
        f"Linhas geradas: {len(lines)}",
        "Colunas usadas: " + ", ".join(FIELD_LABELS.get(f,f) for f in fields),
        "✅ Texto copiado para a área de transferência."
    ]
    if status_widget:
        status_widget.config(state="normal"); status_widget.delete("1.0","end")
        status_widget.insert("end", out + "\n\n" + "\n".join(msg))
        status_widget.config(state="disabled")
    messagebox.showinfo("JSON → Clipboard", "\n".join(msg))

# -------------------------------
# TXT → JSON (módulo existente)
# -------------------------------
def baixar_por_linhas(linhas, pasta_saida: str):
    headers = {"User-Agent": "Jarvis/1.0"}
    os.makedirs(pasta_saida, exist_ok=True)
    total, erros = 0, []
    for i, linha in enumerate(linhas):
        s = linha.strip()
        if s.startswith("JSON: "):
            url = s.replace("JSON: ","").strip()
            try:
                r = requests.get(url, headers=headers, timeout=20)
                r.raise_for_status()
                dados = r.json()
                nome = str(dados.get("title", f"pedido_{i+1}")).replace(" ","_").upper()
                with open(os.path.join(pasta_saida, f"{nome}.json"), "w", encoding="utf-8") as fo:
                    json.dump(dados, fo, ensure_ascii=False, indent=4)
                total += 1
            except Exception as e:
                erros.append(f"{url}\n{e}")
    return total, erros

def exibir_resultado_baixa(total, erros, status_widget=None, destino="JSON"):
    msg = f"{total} arquivo(s) salvos com sucesso na pasta '{destino}'!"
    if erros:
        msg += f"\n\n{len(erros)} erro(s) ocorreram. Veja detalhes no console."
        print("Erros ao baixar JSONs:")
        for e in erros: print("-", e)
    if status_widget:
        status_widget.config(state="normal"); status_widget.delete("1.0","end")
        status_widget.insert("end", msg); status_widget.config(state="disabled")
    messagebox.showinfo("TXT → JSON", msg)

# -------------------------------
# Helpers compartilhados
# -------------------------------
def _clean_drop_path(raw: str) -> Path:
    raw = raw.strip().strip("{}").strip()
    if "}" in raw and "{" in raw: raw = raw.split("} {")[0].strip("{}").strip()
    return Path(raw.strip('"'))

def _status(widget, text):
    if widget:
        widget.config(state="normal"); widget.delete("1.0","end")
        widget.insert("end", text); widget.config(state="disabled")

# -------------------------------
# Tema claro/escuro
# -------------------------------
THEMES = {
    "dark": {"BG": "#0b1220", "PANEL": "#111827", "ACCENT": "#43b7ff", "TEXT": "#e6f0ff", "ENTRY": "#0f172a", "SEL": "#1e3a8a"},
    "light": {"BG": "#f5f7fb", "PANEL": "#ffffff", "ACCENT": "#2563eb", "TEXT": "#0b1220", "ENTRY": "#ffffff", "SEL": "#93c5fd"}
}
CURRENT_THEME = {"name": "dark"}

def theme_colors():
    return THEMES[CURRENT_THEME["name"]]

def apply_base_fonts(root):
    try:
        base_font = tkfont.Font(root, family="Segoe UI", size=10)
    except Exception:
        base_font = tkfont.nametofont("TkDefaultFont")
        base_font.configure(size=10)
    root.option_add("*Font", base_font)

def restyle_all(root, refs):
    C = theme_colors()
    root.configure(bg=C["BG"])
    for w in [refs["outer"], refs["topbar"], refs["content"], refs["bottom"]]:
        w.configure(bg=C["BG"])
    for w in [refs["btn_csvjson"], refs["btn_print"]]:
        w.configure(bg=C["PANEL"], fg=C["TEXT"], relief="solid", bd=1, activebackground=C["SEL"])
    refs["title_lbl"].configure(bg=C["BG"], fg=C["ACCENT"])

# -------------------------------
# MÓDULO 1 — CSV/JSON (sua tela atual)
# -------------------------------
def build_csvjson_frame(parent, dnd_enabled):
    C = theme_colors()
    frame = tk.Frame(parent, bg=C["BG"])
    # Painel
    instr = tk.Label(
        frame,
        text=("Arraste e solte um arquivo .txt ou .json — ou clique em 'Selecionar arquivo…'.\n\n"
              "• TXT → baixa os JSONs para a pasta /JSON/\n• JSON → copia as linhas CSV para a área de transferência"),
        justify="center", bg=C["PANEL"], fg=C["TEXT"]
    )
    instr.grid(row=0, column=0, sticky="ew", pady=(0,8))
    title_lbl = tk.Label(frame, text="COLE O TEXTO AQUI", font=("Segoe UI", 16, "bold"), bg=C["BG"], fg=C["ACCENT"])
    title_lbl.grid(row=1, column=0, sticky="w", pady=(2,4))
    text_box = tk.Text(frame, bg=C["ENTRY"], fg=C["TEXT"], insertbackground=C["ACCENT"], selectbackground=C["SEL"], relief="solid", bd=1)
    text_box.grid(row=2, column=0, sticky="nsew", pady=(0,8))
    status = tk.Text(frame, state="disabled", bg=C["ENTRY"], fg=C["TEXT"], relief="solid", bd=1)
    status.grid(row=3, column=0, sticky="nsew", pady=(0,8))

    # Ações
    bottom = tk.Frame(frame, bg=C["BG"])
    bottom.grid(row=4, column=0, sticky="ew"); bottom.grid_columnconfigure(0, weight=1)
    btn_clear = tk.Button(bottom, text="Limpar área de texto",
                          command=lambda: (text_box.delete("1.0","end"), _status(status,"")),
                          bg=C["PANEL"], fg=C["TEXT"], relief="solid", bd=1)
    btn_clear.grid(row=0, column=0, sticky="w")
    def handle_file(root, file_path):
        try:
            p = _clean_drop_path(file_path)
            if not p.exists() or not p.is_file(): raise FileNotFoundError("Arquivo não encontrado.")
            ext = p.suffix.lower()
            if ext == ".json":
                with p.open("r", encoding="utf-8") as f: data = json.load(f)
                do_convert_json_data(root, data, p.name, status)
            elif ext == ".txt":
                pasta = os.path.join(str(p.parent), "JSON")
                with p.open("r", encoding="utf-8") as f: linhas = f.readlines()
                total, erros = baixar_por_linhas(linhas, pasta)
                exibir_resultado_baixa(total, erros, status, destino="JSON")
            else:
                raise ValueError("Formato não suportado. Use .txt ou .json.")
        except Exception as e:
            _status(status, f"Erro: {e}")
            messagebox.showerror("Erro", str(e))

    btn_select = tk.Button(
        bottom, text="Selecionar arquivo...",
        command=lambda: ((lambda p: handle_file(frame.winfo_toplevel(), p) if p else None)(
            filedialog.askopenfilename(
                title="Selecione .txt ou .json",
                filetypes=[("TXT/JSON","*.txt *.json"), ("TXT","*.txt"), ("JSON","*.json")]
            )
        )),
        bg=C["PANEL"], fg=C["TEXT"], relief="solid", bd=1
    )
    btn_select.grid(row=0, column=1, padx=8)

    btn_process = tk.Button(
        bottom, text="Processar",
        command=lambda: auto_process_pasted(frame.winfo_toplevel(), text_box.get("1.0","end"), status),
        bg=C["ACCENT"], fg=C["TEXT"], relief="flat", bd=0
    )
    btn_process.grid(row=0, column=2)

    # Drag & Drop
    if dnd_enabled:
        instr.drop_target_register(DND_FILES)
        instr.dnd_bind("<<Drop>>", lambda e: handle_file(frame.winfo_toplevel(), e.data))
    else:
        _status(status, "Dica: instale 'tkinterdnd2' para arrastar-e-soltar.")

    frame.grid_columnconfigure(0, weight=1)
    frame.grid_rowconfigure(2, weight=1)
    frame.grid_rowconfigure(3, weight=1)
    return frame

# -------------------------------
# MÓDULO 2 — Impressão (novo)
# -------------------------------
TECIDOS_KNOWN = {
    "DRYFIT","DRY FIT","DRY PESADO","ELASTANO","TACTEL","AEROREADY","RIBANA","TELINHA","OXFORD","FAIXA DE CAPITAO"
}

def _clean_mm_to_m(value_str: str) -> float:
    # Limpeza robusta: remove espaços, pontos de milhar, troca vírgula por ponto → mm
    s = str(value_str).replace(" ", "")
    s = s.replace(".", "")
    s = s.replace(",", ".")
    mm = float(re.sub(r"[^0-9.]", "", s) or "0")
    m = round(mm/1000.0, 2)
    return m

def _guess_tecido_from_name(doc: str) -> str:
    parts = [p.strip() for p in doc.replace(".jpeg","").replace(".jpg","").split(" - ")]
    # 1) tenta o 2º trecho
    if len(parts) >= 2 and parts[1].strip().upper() in TECIDOS_KNOWN:
        return parts[1].strip().upper()
    # 2) tenta qualquer trecho que bata
    for p in parts:
        if p.strip().upper() in TECIDOS_KNOWN:
            return p.strip().upper()
    # 3) último trecho
    return parts[-1].strip().upper() if parts else doc.upper()

def parse_log_txt(path: Path):
    # Lê um arquivo .txt de log "genérico" e extrai campos relevantes
    raw = path.read_text(encoding="utf-8", errors="ignore")
    d = {}
    # Suporta variantes: Document=..., PrintHeightMM=..., StartTime=..., EndTime=...
    m = re.search(r"Document\s*=\s*(.+)", raw)
    d["Document"] = (m.group(1).strip() if m else path.name)
    m = re.search(r"PrintHeightMM\s*=\s*([0-9\.\,\s]+)", raw)
    d["Altura_m"] = _clean_mm_to_m(m.group(1)) if m else 0.0
    ms = re.search(r"StartTime\s*=\s*(.+)", raw)
    me = re.search(r"EndTime\s*=\s*(.+)", raw)
    def _fmt_time(val, fallback="--:--"):
        if not val: return fallback
        # tenta parse flexível
        try:
            dt = datetime.fromisoformat(val.strip().replace("Z","").replace("/", "-"))
            return dt.strftime("%H:%M"), dt.strftime("%d/%m/%Y")
        except Exception:
            # tenta hh:mm diretamente
            mm = re.search(r"(\d{2}:\d{2})", val)
            hhmm = mm.group(1) if mm else fallback
            return hhmm, ""
    inicio, data1 = _fmt_time(ms.group(1) if ms else "")
    fim, data2 = _fmt_time(me.group(1) if me else "")
    d["Inicio"] = inicio
    d["Fim"]    = fim
    d["Data"]   = data1 or data2 or datetime.now().strftime("%d/%m/%Y")
    d["Tecido"] = _guess_tecido_from_name(d["Document"])
    return d

def apply_discounts(rows):
    """
    rows: lista de dicts na ordem real do rolo (topo = último impresso).
    Regras:
      - formar blocos consecutivos por Tecido
      - último bloco NÃO recebe desconto
      - cada bloco anterior recebe −1,00 m no último item do bloco (propaga para cima se <1,00)
      - se houver tecido repetido em blocos diferentes, cada bloco (exceto o último) recebe −1
      - rolo com 1 bloco: sem desconto
    """
    if not rows: return rows, []

    # Identifica blocos [start_idx, end_idx] por tecido
    blocks = []
    start = 0
    for i in range(1, len(rows)+1):
        if i == len(rows) or rows[i]["Tecido"] != rows[i-1]["Tecido"]:
            blocks.append((start, i-1, rows[i-1]["Tecido"]))
            start = i

    if len(blocks) <= 1:
        return rows, []  # um bloco só: sem desconto

    discount_marks = []  # índices de linhas que receberam desconto (para observação visual)

    # Aplica desconto em todos os blocos menos o último
    for bi, (s, e, tecido) in enumerate(blocks):
        if bi == len(blocks)-1:
            continue  # último bloco sem desconto
        # aplicar -1 no último item do bloco (e propagar)
        remaining = 1.00
        idx = e
        while remaining > 1e-9 and idx >= s:
            val = rows[idx]["Altura_m"]
            if val <= remaining:
                if val > 0:
                    rows[idx]["Altura_m"] = 0.00
                    discount_marks.append(idx)
                    remaining = round(remaining - val, 2)
                idx -= 1
            else:
                rows[idx]["Altura_m"] = round(val - remaining, 2)
                discount_marks.append(idx)
                remaining = 0.0

    return rows, sorted(set(discount_marks))

def build_print_frame(parent):
    C = theme_colors()
    frame = tk.Frame(parent, bg=C["BG"])
    frame.grid_columnconfigure(0, weight=1)
    frame.grid_rowconfigure(1, weight=1)

    # Top controls
    top = tk.Frame(frame, bg=C["BG"])
    top.grid(row=0, column=0, sticky="ew", pady=(0,8))
    lbl = tk.Label(top, text="Impressão — selecione logs (.txt)", bg=C["BG"], fg=C["TEXT"])
    lbl.pack(side="left")

    files = []

    def add_files():
        sel = filedialog.askopenfilenames(title="Selecione logs .txt", filetypes=[("Logs .txt", "*.txt")])
        if not sel: return
        for p in sel:
            files.append(Path(p))
            listbox.insert("end", os.path.basename(p))

    def clear_files():
        files.clear()
        listbox.delete(0, "end")
        _status(txt, "")

    btn_add = tk.Button(top, text="Adicionar logs…", command=add_files, bg=C["PANEL"], fg=C["TEXT"], relief="solid", bd=1)
    btn_add.pack(side="left", padx=6)
    btn_clear = tk.Button(top, text="Limpar lista", command=clear_files, bg=C["PANEL"], fg=C["TEXT"], relief="solid", bd=1)
    btn_clear.pack(side="left")

    # Listagem de arquivos + saída
    mid = tk.Frame(frame, bg=C["BG"])
    mid.grid(row=1, column=0, sticky="nsew")
    mid.grid_columnconfigure(1, weight=1)
    mid.grid_rowconfigure(0, weight=1)

    listbox = tk.Listbox(mid)
    listbox.grid(row=0, column=0, sticky="nsw", padx=(0,8))

    txt = tk.Text(mid, state="disabled", bg=C["ENTRY"], fg=C["TEXT"], insertbackground=C["ACCENT"], relief="solid", bd=1)
    txt.grid(row=0, column=1, sticky="nsew")

    def preview():
        if not files:
            messagebox.showinfo("Impressão", "Adicione pelo menos um log .txt.")
            return
        # Parse
        rows = []
        for p in files:
            try:
                rows.append(parse_log_txt(p))
            except Exception as e:
                messagebox.showwarning("Aviso", f"Falhou ao ler {p.name}:\n{e}")
        # Ordena por StartTime decrescente se disponível (último impresso primeiro).
        # Sem timestamp confiável, mantém ordem adicionada (você pode mudar aqui).
        # Aplica descontos
        rows, marks = apply_discounts(rows)

        # Render
        def fmt(m):
            return f"{m:.2f}".replace(".", ",")

        # Cabeçalho
        txt.config(state="normal"); txt.delete("1.0","end")
        data_header = rows[0]["Data"] if rows else datetime.now().strftime("%d/%m/%Y")
        txt.insert("end", f"📅 Data: {data_header}\n")
        txt.insert("end", "🧾 TABELA COMPLETA (ordem real do rolo)\n")
        txt.insert("end", "| Ordem | Documento | Tecido | Início | Fim | Altura (m) | Observação |\n")
        txt.insert("end", "|------:|-----------|--------|:-----:|:---:|-----------:|------------|\n")
        for i, r in enumerate(rows, start=1):
            obs = "(-1 m aplicado)" if (i-1) in marks else "—"
            doc = r["Document"]
            # quebra “Documento” em duas linhas se for muito longo (35+ chars)
            if len(doc) > 35:
                # quebra na última whitespace antes do limite
                cut = doc.rfind(" ", 0, 35)
                if cut == -1: cut = 35
                doc1, doc2 = doc[:cut].strip(), doc[cut:].strip()
                doc_show = f"**{doc1}**<br>**{doc2}**"
            else:
                doc_show = f"**{doc}**"
            txt.insert("end", f"| {i:<5} | {doc_show} | {r['Tecido']} | {r['Inicio']} | {r['Fim']} | {fmt(r['Altura_m'])} | {obs} |\n")

        # Resumo por tecido
        totals = {}
        for r in rows:
            totals[r["Tecido"]] = round(totals.get(r["Tecido"], 0.0) + r["Altura_m"], 2)
        txt.insert("end", "📊 RESUMO POR TECIDO (líquido)\n")
        txt.insert("end", "| Tecido | Total (m) |\n|--------|-----------:|\n")
        for t, v in totals.items():
            txt.insert("end", f"| {t} | {fmt(v)} |\n")
        txt.insert("end", f"\nQuantidade de tecidos no rolo: {len(totals)}\n")
        txt.config(state="disabled")

    def fechar(machine):
        # Aqui você chama seu pipeline de fechamento:
        # - reprocessa rows (sem observação)
        # - gera ROLO_ID
        # - gera PDF normal e espelhado (usando seu gerador)
        # Nesta versão de exemplo, vamos só avisar.
        messagebox.showinfo("Fechar rolo", f"Gerar PDFs (Normal + Espelhado) para {machine}.\nIntegrar com seu gerador de PDF aqui.")

    bot = tk.Frame(frame, bg=C["BG"])
    bot.grid(row=2, column=0, sticky="ew", pady=(8,0))
    btn_prev = tk.Button(bot, text="Pré-visualizar", command=preview, bg=C["ACCENT"], fg=C["TEXT"], relief="flat")
    btn_prev.pack(side="left")
    tk.Label(bot, text="  |  ", bg=C["BG"], fg=C["TEXT"]).pack(side="left")
    tk.Button(bot, text="Fechar M1", command=lambda: fechar("M1"), bg=C["PANEL"], fg=C["TEXT"], relief="solid", bd=1).pack(side="left", padx=4)
    tk.Button(bot, text="Fechar M2", command=lambda: fechar("M2"), bg=C["PANEL"], fg=C["TEXT"], relief="solid", bd=1).pack(side="left")

    # DnD na listbox (opcional)
    if DND_AVAILABLE:
        listbox.drop_target_register(DND_FILES)
        def on_drop(e):
            p = _clean_drop_path(e.data)
            if p.is_file() and p.suffix.lower()==".txt":
                files.append(p); listbox.insert("end", os.path.basename(p))
        listbox.dnd_bind("<<Drop>>", on_drop)

    return frame

# -------------------------------
# UI com alternância de módulos
# -------------------------------
def build_ui():
    Root = TkinterDnD.Tk if DND_AVAILABLE else tk.Tk
    root = Root()
    root.title(APP_TITLE)
    root.geometry("1100x780")
    root.minsize(920, 620)
    root.resizable(True, True)
    try:
        root.iconbitmap(resource_path("Jarvis.ico"))
    except Exception:
        pass
    apply_base_fonts(root)

    # Esqueleto
    outer = tk.Frame(root); outer.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
    root.grid_rowconfigure(0, weight=1); root.grid_columnconfigure(0, weight=1)
    outer.grid_rowconfigure(2, weight=1); outer.grid_columnconfigure(0, weight=1)

    # TopBar com seletor de módulo
    topbar = tk.Frame(outer); topbar.grid(row=0, column=0, sticky="ew", pady=(0,8))
    title_lbl = tk.Label(topbar, text="Jarvis — Módulos", font=("Segoe UI", 16, "bold"))
    title_lbl.pack(side="left")

    btn_csvjson = tk.Button(topbar, text="CSV/JSON")
    btn_print   = tk.Button(topbar, text="Impressão")
    btn_csvjson.pack(side="right", padx=4)
    btn_print.pack(side="right")

    # Área de conteúdo (stack)
    content = tk.Frame(outer); content.grid(row=2, column=0, sticky="nsew")

    frame_csv = build_csvjson_frame(content, DND_AVAILABLE)
    frame_print = build_print_frame(content)
    for f in (frame_csv, frame_print):
        f.grid(row=0, column=0, sticky="nsew")

    # Alternância
    def show_frame(which):
        frame_csv.grid_remove()
        frame_print.grid_remove()
        if which == "csv":
            frame_csv.grid()
        else:
            frame_print.grid()
    show_frame("csv")  # módulo inicial

    btn_csvjson.configure(command=lambda: show_frame("csv"))
    btn_print.configure(command=lambda: show_frame("print"))

    # Rodapé
    bottom = tk.Frame(outer); bottom.grid(row=3, column=0, sticky="ew", pady=(8,0))
    # tema
    btn_toggle = tk.Button(bottom, text=f"Tema: Escuro")
    btn_toggle.pack(side="left")

    refs = {"outer":outer,"topbar":topbar,"content":content,"bottom":bottom,
            "btn_csvjson":btn_csvjson,"btn_print":btn_print,"title_lbl":title_lbl}
    restyle_all(root, refs)
    btn_toggle.configure(command=lambda: (CURRENT_THEME.update({"name": "light" if CURRENT_THEME["name"]=="dark" else "dark"}),
                                          restyle_all(root, refs),
                                          btn_toggle.configure(text=f"Tema: {'Escuro' if CURRENT_THEME['name']=='dark' else 'Claro'}")),
                         text=f"Tema: {'Escuro' if CURRENT_THEME['name']=='dark' else 'Claro'}")
    return root

# -------------------------------
def auto_process_pasted(root, raw_text, status_widget=None):
    text = raw_text.strip()
    if not text:
        messagebox.showwarning("Aviso", "Cole algum conteúdo no campo de texto.")
        return
    if text[0] in "{[":
        try:
            data = json.loads(text)
        except Exception as e:
            messagebox.showerror("Erro", f"Não consegui interpretar o texto como JSON:\n{e}")
            return
        do_convert_json_data(root, data, "Conteúdo colado", status_widget)
        return
    target_dir = filedialog.askdirectory(title="Escolha a pasta onde será criada a subpasta 'JSON'")
    if not target_dir:
        return
    pasta_saida = os.path.join(target_dir, "JSON")
    linhas = text.splitlines()
    total, erros = baixar_por_linhas(linhas, pasta_saida)
    exibir_resultado_baixa(total, erros, status_widget, destino="JSON")

# -------------------------------
def main():
    root = build_ui()
    root.mainloop()

if __name__ == "__main__":
    main()
