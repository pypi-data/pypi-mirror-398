# Copyright 2025 w.Sanice
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import re
import unidecode
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import joblib
import logging

from sklearn.preprocessing import MinMaxScaler, StandardScaler
from sqlalchemy import create_engine

logger = logging.getLogger('Sanice')
logger.setLevel(logging.INFO)

if not logger.handlers:
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

class Sanice:
    """
    S.A.N.I.C.E.
    (Sistema Automatizado de Normalização, Inteligência Computacional e Estatística)
    -----------------------------------------------------------------------------
    Framework para limpar, transformar e modelar dados automaticamente.
    """
    I18N = {
        "pt": {
            "auto_date": "[SMART] Data detectada e convertida na coluna: '{col}'",
            "auto_mem": "[SMART] Memória otimizada! {n} colunas convertidas para 'category'.",
            "mongo_ok": "[MONGO] Dados exportados para coleção '{col}' com sucesso.",
            "sql_read_ok": "[SQL] Li {rows} linhas da consulta SQL.",
            "load_ok": "[CARREGAR] Dados carregados: {rows} linhas x {cols} colunas.",
            "load_err": "[ERRO] Falha ao carregar: {e}",
            "view": "\n[VISUALIZAR] {header}:",
            "clean_cols": "[LIMPEZA] Nomes das colunas padronizados.",
            "clean_txt": "[LIMPEZA] Texto da coluna '{col}' normalizado.",
            "drop_null": "[REMOVER] {qtd} linhas com nulos removidas.",
            "fill_null": "[PREENCHER] Nulos preenchidos com '{val}'.",
            "date_conv": "[DATA] Coluna '{col}' convertida para data.",
            "col_add": "[CRIAR] Coluna '{col}' criada.",
            "filter": "[FILTRO] '{query}': {before} -> {after} linhas.",
            "sort": "[ORDENAR] Ordenado por {cols}.",
            "join": "[UNIR] Tabelas unidas ({how}). Linhas: {before} -> {after}",
            "plot_err": "[ERRO] Falha ao plotar: {e}",
            "stats": "\n[ESTATÍSTICAS] Resumo Estatístico:",
            "types": "\n[TIPOS] Tipos de Dados:",
            "save": "[SALVAR] Arquivo salvo em: {path}",
            "ml_start": "\n[AUTO-ML] Iniciando treinamento para prever: '{target}'...",
            "ml_ignore_date": "   [INFO] Ignorando colunas de data crua: {cols}",
            "ml_feats": "   - Features processadas: {n} colunas (após encoding).",
            "ml_success_clf": "   Modelo Classificador treinado!",
            "ml_success_reg": "   Modelo Regressor treinado!",
            "ml_acc": "   Acurácia: {score:.2%}",
            "ml_r2": "   R² Score: {score:.4f}",
            "ml_saved": "   Modelo salvo em: {path}",
            "ia_loaded": "[IA] Modelo carregado! Espera {n} colunas.",
            "pred_done": "[PREVISÃO] Previsões geradas na coluna '{col}'.",
            "err_load_ia": "Você precisa usar .carregar_ia() antes de prever!",
            "sql_ok": "[SQL] Tabela '{tb}' exportada com sucesso para o banco.",
            "sql_err": "[SQL] Erro ao exportar: {e}",
            "scale_ok": "[ESCALA] Dados normalizados usando '{method}'.",
            "outlier_rem": "[OUTLIERS] {qtd} outliers removidos (Método IQR).",
            "api_start": "[API] Servidor iniciado em http://127.0.0.1:8000/docs",
            "trans_money": "[TRANSFORMAR] '{col}' convertida para Moeda (float).",
            "trans_num": "[TRANSFORMAR] '{col}' limpa (apenas dígitos).",
            "trans_email": "[TRANSFORMAR] '{col}' normalizada para E-mail.",
            "trans_date": "[TRANSFORMAR] '{col}' convertida para Data.",
            "trans_err": "[ERRO] Regra '{rule}' desconhecida ou falha.",
            "select_ok": "[SELEÇÃO] Mantidas {n} colunas.",
            "select_warn": "[AVISO] Colunas não encontradas e ignoradas: {cols}",
            "help_title": "\n[AJUDA] Comandos disponíveis em '{lang}':\n",
            "ml_tourn": "   [AUTO-ML] Avaliando {n} modelos (Linear, RF, Gradient)...",
            "ml_win": "   [RESULTADO] Melhor modelo: {name} | {metric}: {score:.4f}",
            "ml_fail": "   [ERRO] Falha no modelo {name}: {e}",
        },
        "en": {
            "auto_date": "[SMART] Date detected and converted in column: '{col}'",
            "auto_mem": "[SMART] Memory optimized! {n} columns converted to 'category'.",
            "mongo_ok": "[MONGO] Data exported to collection '{col}' successfully.",
            "sql_read_ok": "[SQL] Read {rows} rows from SQL query.",
            "load_ok": "[LOAD] Data loaded: {rows} rows x {cols} cols.",
            "load_err": "[ERROR] Failed to load: {e}",
            "view": "\n[VIEW] {header}:",
            "clean_cols": "[CLEAN] Column names standardized.",
            "clean_txt": "[CLEAN] Text in column '{col}' normalized.",
            "drop_null": "[DROP] {qtd} rows with nulls removed.",
            "fill_null": "[FILL] Nulls filled with '{val}'.",
            "date_conv": "[DATE] Column '{col}' converted to datetime.",
            "col_add": "[ADD] Column '{col}' created.",
            "filter": "[FILTER] '{query}': {before} -> {after} rows.",
            "sort": "[SORT] Sorted by {cols}.",
            "join": "[JOIN] Tables merged ({how}). Rows: {before} -> {after}",
            "plot_err": "[ERROR] Failed to plot: {e}",
            "stats": "\n[STATS] Statistical Summary:",
            "types": "\n[TYPES] Data Types:",
            "save": "[SAVE] File saved at: {path}",
            "ml_start": "\n[AUTO-ML] Starting training to predict: '{target}'...",
            "ml_ignore_date": "   [INFO] Ignoring raw date columns: {cols}",
            "ml_feats": "   - Features processed: {n} cols (after encoding).",
            "ml_success_clf": "   Classifier Model trained!",
            "ml_success_reg": "   Regressor Model trained!",
            "ml_acc": "   Accuracy: {score:.2%}",
            "ml_r2": "   R² Score: {score:.4f}",
            "ml_saved": "   Shielded model saved at: {path}",
            "ia_loaded": "[AI] Model loaded! Expects {n} columns.",
            "pred_done": "[PREDICT] Predictions generated in column '{col}'.",
            "err_load_ia": "You need to use .load_ai() before predicting!",
            "sql_ok": "[SQL] Table '{tb}' successfully exported to database.",
            "sql_err": "[SQL] Error exporting: {e}",
            "scale_ok": "[SCALE] Data normalized using '{method}'.",
            "outlier_rem": "[OUTLIERS] {qtd} outliers removed (IQR Method).",
            "api_start": "[API] Server started at http://127.0.0.1:8000/docs",
            "trans_money": "[TRANSFORM] '{col}' converted to Currency (float).",
            "trans_num": "[TRANSFORM] '{col}' cleaned (digits only).",
            "trans_email": "[TRANSFORM] '{col}' normalized to E-mail.",
            "trans_date": "[TRANSFORM] '{col}' converted to Date.",
            "trans_err": "[ERROR] Rule '{rule}' unknown or failed.",
            "help_title": "\n[HELP] Available commands in '{lang}':\n",
            "select_ok": "[SELECT] Kept {n} columns.",
            "select_warn": "[WARN] Columns not found and ignored: {cols}",
            "ml_tourn": "   [AUTO-ML] Evaluating {n} models (Linear, RF, Gradient)...",
            "ml_win": "   [RESULT] Best model: {name} | {metric}: {score:.4f}",
            "ml_fail": "   [ERROR] Model {name} failed: {e}",
        },
        "zh": {
            "auto_date": "[智能] 检测到日期并已转换列：'{col}'",
            "auto_mem": "[智能] 内存已优化！{n} 列已转换为 'category'。",
            "mongo_ok": "[MONGO] 数据已成功导出到集合 '{col}'。",
            "sql_read_ok": "[SQL] 从 SQL 查询中读取了 {rows} 行。",
            "load_ok": "[加载] 数据已加载：{rows} 行 x {cols} 列。",
            "load_err": "[错误] 加载失败：{e}",
            "view": "\n[查看] {header}：",
            "clean_cols": "[清洗] 列名已标准化。",
            "clean_txt": "[清洗] 列 '{col}' 的文本已规范化。",
            "drop_null": "[移除] 已移除 {qtd} 行空值。",
            "fill_null": "[填充] 空值已填充为 '{val}'。",
            "date_conv": "[日期] 列 '{col}' 已转换为日期格式。",
            "col_add": "[创建] 列 '{col}' 已创建。",
            "filter": "[过滤] '{query}': {before} -> {after} 行。",
            "sort": "[排序] 按 {cols} 排序。",
            "join": "[合并] 表格已合并 ({how})。行数: {before} -> {after}",
            "plot_err": "[错误] 绘图失败：{e}",
            "stats": "\n[统计] 统计摘要：",
            "types": "\n[类型] 数据类型：",
            "save": "[保存] 文件已保存至：{path}",
            "ml_start": "\n[自动机器学习] 开始训练预测：'{target}'...",
            "ml_ignore_date": "   [信息] 忽略原始日期列：{cols}",
            "ml_feats": "   - 特征处理：{n} 列（编码后）。",
            "ml_success_clf": "   分类模型训练完成！",
            "ml_success_reg": "   回归模型训练完成！",
            "ml_acc": "   准确率：{score:.2%}",
            "ml_r2": "   R² 分数：{score:.4f}",
            "ml_saved": "   模型已保存至：{path}",
            "ia_loaded": "[AI] 模型已加载！预期 {n} 列。",
            "pred_done": "[预测] 预测结果已生成在 '{col}' 列。",
            "err_load_ia": "预测前请先使用 .load_ai()！",
            "sql_ok": "[SQL] 表 '{tb}' 已成功导出到数据库。",
            "sql_err": "[SQL] 导出错误：{e}",
            "scale_ok": "[缩放] 数据已使用 '{method}' 标准化。",
            "outlier_rem": "[异常值] 已移除 {qtd} 个异常值 (IQR 方法)。",
            "api_start": "[API] 服务器已启动 http://127.0.0.1:8000/docs",
            "trans_money": "[转换] '{col}' 已转换为货币 (float)。",
            "trans_num": "[转换] '{col}' 已清洗 (仅数字)。",
            "trans_email": "[转换] '{col}' 已标准化为电子邮件。",
            "trans_date": "[转换] '{col}' 已转换为日期。",
            "trans_err": "[错误] 规则 '{rule}' 未知或失败。",
            "help_title": "\n[帮助] '{lang}' 可用命令：\n",
            "select_ok": "[选择] 保留了 {n} 列。",
            "select_warn": "[警告] 未找到并已忽略的列：{cols}",
            "ml_tourn": "   [AUTO-ML] 正在评估 {n} 个模型...",
            "ml_win": "   [结果] 最佳模型: {name} ({metric}: {score:.4f})",
            "ml_fail": "   [错误] 模型 {name} 失败: {e}",
        },
        "hi": {
            "auto_date": "[SMART] '{col}' mein date mili aur convert ho gayi.",
            "auto_mem": "[SMART] Memory bachayi gayi! {n} columns 'category' ban gaye.",
            "mongo_ok": "[MONGO] Data '{col}' collection mein export ho gaya.",
            "sql_read_ok": "[SQL] SQL query se {rows} rows padhe gaye.",
            "load_ok": "[LOAD] Data load ho gaya: {rows} rows x {cols} cols.",
            "load_err": "[ERROR] Load karne mein fail: {e}",
            "view": "\n[DEKHE] {header}:",
            "clean_cols": "[SAFAI] Column ke naam standardize kiye gaye.",
            "clean_txt": "[SAFAI] Column '{col}' ka text theek kiya gaya.",
            "drop_null": "[HATAYE] {qtd} rows null hataye gaye.",
            "fill_null": "[BHARE] Nulls ko '{val}' se bhara gaya.",
            "date_conv": "[TARIKH] Column '{col}' date mein badla gaya.",
            "col_add": "[BANAYE] Column '{col}' banaya gaya.",
            "filter": "[FILTER] '{query}': {before} -> {after} rows.",
            "sort": "[SORT] {cols} ke hisaab se sort kiya.",
            "join": "[JODE] Tables jode gaye ({how}). Rows: {before} -> {after}",
            "plot_err": "[ERROR] Plot karne mein fail: {e}",
            "stats": "\n[STATS] Sankhyiki Saar:",
            "types": "\n[TYPES] Data Types:",
            "save": "[SAVE] File save kiya gaya: {path}",
            "ml_start": "\n[AUTO-ML] Training shuru: '{target}'...",
            "ml_ignore_date": "   [INFO] Raw date columns ignore kar rahe hain: {cols}",
            "ml_feats": "   - Features processed: {n} cols (encoding ke baad).",
            "ml_success_clf": "   Model train ho gaya (Classifier)!",
            "ml_success_reg": "   Model train ho gaya (Regressor)!",
            "ml_acc": "   Accuracy: {score:.2%}",
            "ml_r2": "   R² Score: {score:.4f}",
            "ml_saved": "   Model save kiya gaya: {path}",
            "ia_loaded": "[AI] Model load hua! {n} columns chahiye.",
            "pred_done": "[PREDICT] Bhavishya '{col}' mein likha gaya.",
            "err_load_ia": "Predict karne se pehle .load_ai() use karein!",
            "sql_ok": "[SQL] Table '{tb}' database mein export ho gaya.",
            "sql_err": "[SQL] Export mein galti: {e}",
            "scale_ok": "[SCALE] Data '{method}' se normalize kiya gaya.",
            "outlier_rem": "[OUTLIERS] {qtd} outliers hataye gaye (IQR Method).",
            "api_start": "[API] Server shuru hua http://127.0.0.1:8000/docs par",
            "trans_money": "[BADLAV] '{col}' currency (float) mein badla gaya.",
            "trans_num": "[BADLAV] '{col}' saaf kiya gaya (keval ank).",
            "trans_email": "[BADLAV] '{col}' E-mail ke liye theek kiya gaya.",
            "trans_date": "[BADLAV] '{col}' Tarikh mein badla gaya.",
            "trans_err": "[ERROR] Rule '{rule}' galat hai ya fail ho gayi.",
            "help_title": "\n[MADAD] '{lang}' mein commands:\n",
            "select_ok": "[CHUNNA] {n} columns rakhi gayin.",
            "select_warn": "[CHETAVANI] Columns nahi mili aur ignore ki gayi: {cols}",
            "ml_tourn": "   [AUTO-ML] {n} models ka mulyankan (evaluation) ho raha hai...",
            "ml_win": "   [NATIJA] Behtarin model: {name} ({metric}: {score:.4f})",
            "ml_fail": "   [GALTI] Model {name} fail hua: {e}",
        }
    }

    METHOD_ALIASES = {
        "exportar_mongo":    ["export_mongo", "导出Mongo", "mongo_bheje"],
        "corrigir_colunas":  ["fix_columns", "修正列名", "column_sudhare"],
        "limpar_texto":      ["clean_text",       "清洗文本",   "text_safai"],
        "remover_nulos":     ["remove_nulls",     "移除空值",   "null_hataye"],
        "converter_data":    ["convert_date",     "转换日期",   "date_badlo"],
        "criar_coluna":      ["create_column",    "创建列",     "column_banaye"],
        "filtrar":           ["filter_data",      "过滤数据",   "filter_kare"],
        "ordenar":           ["sort_data",        "排序数据",   "sort_kare"],
        "unir":              ["join_data",        "合并数据",   "jode"],
        "plotar":            ["plot_chart",       "绘制图表",   "graph_banaye"],
        "resumo_estatistico":["stats_summary",    "统计摘要",   "stats_dekhe"],
        "salvar":            ["save_file",        "保存文件",   "save_kare"],
        "auto_ml":           ["train_automl",     "自动训练",   "automl_kare"],
        "carregar_ia":       ["load_ai",          "加载模型",   "ai_load_kare"],
        "prever":            ["predict",          "预测",       "bhavishya_bataye"],
        "ver":               ["view",             "查看",       "dekhe"],
        "ajuda":             ["help",             "帮助",       "madad"],
        "agrupar":           ["group_by",          "分组",       "samuh_banaye"],
        "tabela_dinamica":   ["pivot_table",       "透视表",     "pivot_table"],
        "exportar_sql":      ["export_sql",        "导出SQL",    "sql_export"],
        "matriz_correlacao": ["correlation_matrix","相关矩阵",   "sambandh_matrix"],
        "tratar_outliers":   ["handle_outliers",   "处理异常值", "outliers_hataye"],
        "escalonar":         ["scale_data",        "数据缩放",   "scale_kare"],
        "servir_api":        ["serve_api",         "启动API",    "api_chalu_kare"],
        "transformar":       ["transform",         "数据转换",   "badlav_kare"],
        "configurar_logs": ["configure_logs", "配置日志", "log_set_kare"],
        "selecionar_colunas": ["select_columns", "选择列", "columns_chunne"],
        "pegar_dataframe": ["get_dataframe", "获取数据", "data_lo"]
    }
    
    VERBOSITY_MAP = {
        "silent": logging.CRITICAL + 1,
        "error": logging.ERROR,
        "warn": logging.WARNING,
        "info": logging.INFO,
        "debug": logging.DEBUG
    }

    CURRENCY_MAP = {
        "pt": "BRL",
        "en": "USD",
        "zh": "CNY",
        "hi": "INR",
    }

    def __init__(self, fonte_dados, lang="pt", smart_run=False, currency=None):
        self.lang = lang
        self.df = None
        self.scaler = None
        moeda_padrao = self.CURRENCY_MAP.get(self.lang, "USD")
        self.currency = currency.upper() if currency else moeda_padrao
        
        self._setup_aliases()

        try:
            if isinstance(fonte_dados, pd.DataFrame):
                self.df = fonte_dados.copy()
            elif isinstance(fonte_dados, str):
                if fonte_dados.endswith('.csv'): self.df = pd.read_csv(fonte_dados)
                elif fonte_dados.endswith(('.xls', '.xlsx')): self.df = pd.read_excel(fonte_dados)
                elif fonte_dados.endswith('.parquet'): self.df = pd.read_parquet(fonte_dados)
                elif fonte_dados.endswith('.json'): self.df = pd.read_json(fonte_dados)
                        
            if self.df is not None:
                self._log("load_ok", rows=self.df.shape[0], cols=self.df.shape[1])
                if smart_run:
                    self._tentar_converter_datas()
                    self._otimizar_memoria()
            else:
                raise ValueError("Format not supported / Formato não suportado.")
                
        except Exception as e:
            self._log("load_err", e=str(e))

    @classmethod
    def de_sql(cls, url_conexao, query, lang="pt"):
        try:
            engine = create_engine(url_conexao)
            df = pd.read_sql(query, engine)
            instancia = cls(fonte_dados=df, lang=lang)
            instancia._log("sql_read_ok", rows=len(df))
            return instancia
            
        except Exception as e:
            print(f"[ERRO SQL] {e}")
            return None

    from_sql = de_sql
    从SQL = de_sql
    sql_se = de_sql

    def configurar_logs(self, nivel="info"):
        nivel_log = self.VERBOSITY_MAP.get(nivel.lower(), logging.INFO)
        logger.setLevel(nivel_log)
        
        if nivel.lower() != 'silent':
            print(f"[LOG] Sanice configurado para nível: {nivel.upper()}")
        
        return self
    
    def _log(self, key, **kwargs):
        lang_dict = self.I18N.get(self.lang, self.I18N["en"])
        msg = lang_dict.get(key, self.I18N["en"].get(key, ""))
        
        if msg:
            logger.info(msg.format(**kwargs))

    def _setup_aliases(self):
        if self.lang == "pt": return
        idx_map = {"en": 0, "zh": 1, "hi": 2}
        idx = idx_map.get(self.lang, 0)
        for metodo_pt, aliases in self.METHOD_ALIASES.items():
            try:
                alias_name = aliases[idx]
                metodo_original = getattr(self, metodo_pt)
                setattr(self, alias_name, metodo_original)
            except IndexError:
                pass


    def _tentar_converter_datas(self):
        colunas_texto = self.df.select_dtypes(include=['object']).columns
    
        for col in colunas_texto:
            temp = pd.to_datetime(self.df[col], errors='coerce')
            nao_nulos = self.df[col].dropna().shape[0]
            if nao_nulos > 0:
                validos = temp.dropna().shape[0]
                taxa_sucesso = validos / nao_nulos
                
                if taxa_sucesso > 0.8:
                    self.df[col] = temp
                    self._log("auto_date", col=col)

    def _otimizar_memoria(self):
        colunas_texto = self.df.select_dtypes(include=['object']).columns
        convertidas = 0
        total_linhas = len(self.df)
        
        for col in colunas_texto:
            unicos = self.df[col].nunique()
            if total_linhas > 100 and (unicos / total_linhas) < 0.5:
                self.df[col] = self.df[col].astype('category')
                convertidas += 1
        
        if convertidas > 0:
            self._log("auto_mem", n=convertidas)

    def ajuda(self):
        self._log("help_title", lang=self.lang)
        if self.lang == "pt":
            cmds = [m for m in self.METHOD_ALIASES.keys()]
        else:
            idx_map = {"en": 0, "zh": 1, "hi": 2}
            idx = idx_map.get(self.lang, 0)
            cmds = [aliases[idx] for aliases in self.METHOD_ALIASES.values()]
        print(", ".join([f".{c}()" for c in cmds]))
        return self

    def ver(self, linhas=5, titulo=None):
        if self.df is not None:
            header = titulo if titulo else f"Top {linhas}"
            self._log("view", header=header)
            print(self.df.head(linhas))
        return self

    def corrigir_colunas(self):
        if self.df is not None:
            old_cols = self.df.columns
            new_cols = [unidecode.unidecode(c).strip().lower() for c in old_cols] 
            new_cols = [c.replace(" ", "_").replace("/", "_").replace("-", "_") for c in new_cols] 
            new_cols = [re.sub(r'[^a-z0-9_]+', '', c) for c in new_cols]
            self.df.rename(columns={o: n for o, n in zip(old_cols, new_cols)}, inplace=True)
            self._log("clean_cols")
        return self

    def limpar_texto(self, colunas):
        if isinstance(colunas, str): colunas = [colunas]
        for col in colunas:
            if col in self.df.columns:
                self.df[col] = [str(x).strip().title() if pd.notnull(x) else x for x in self.df[col]]
                self._log("clean_txt", col=col)
        return self

    def remover_nulos(self, estrategia="apagar", preencher_com=0):
        antes = len(self.df)
        if estrategia == "apagar":
            self.df.dropna(inplace=True)
            self._log("drop_null", qtd=antes - len(self.df))
        elif estrategia == "preencher":
            self.df.fillna(preencher_com, inplace=True)
            self._log("fill_null", val=preencher_com)
        return self

    def converter_data(self, colunas, formato=None):
        if isinstance(colunas, str): colunas = [colunas]
        for col in colunas:
            self.df[col] = pd.to_datetime(self.df[col], format=formato, errors='coerce')
            self._log("date_conv", col=col)
        return self

    def criar_coluna(self, nome_nova_col, expressao_ou_func):
        try:
            if callable(expressao_ou_func):
                self.df[nome_nova_col] = self.df.apply(expressao_ou_func, axis=1)
            elif isinstance(expressao_ou_func, str):
                self.df.eval(f"{nome_nova_col} = {expressao_ou_func}", inplace=True)

            self._log("col_add", col=nome_nova_col)
            return self

        except Exception as e:
            self._log("load_err", e=str(e))

    
    def filtrar(self, query_string):
        try:
            antes = len(self.df)
            self.df = self.df.query(query_string)
            self._log("filter", query=query_string, before=antes, after=len(self.df))
        except Exception as e:
            print(f"Query Error: {e}")
        return self

    def ordenar(self, colunas, ascendente=True):
        self.df.sort_values(by=colunas, ascending=ascendente, inplace=True)
        self._log("sort", cols=colunas)
        return self

    def unir(self, outro_df, chaves, como="inner"):
        tabela_direita = outro_df.df if isinstance(outro_df, Sanice) else outro_df
        antes = len(self.df)
        self.df = pd.merge(self.df, tabela_direita, on=chaves, how=como)
        self._log("join", how=como, before=antes, after=len(self.df))
        return self

    def plotar(self, tipo="barras", x=None, y=None, hue=None, titulo=None):
        plt.figure(figsize=(10, 6))
        sns.set_theme(style="whitegrid")
        try:
            if tipo in ["barras", "bar"]: sns.barplot(data=self.df, x=x, y=y, hue=hue, palette="viridis")
            elif tipo in ["linha", "line"]: sns.lineplot(data=self.df, x=x, y=y, hue=hue)
            elif tipo in ["scatter", "dispersao"]: sns.scatterplot(data=self.df, x=x, y=y, hue=hue, alpha=0.7)
            elif tipo in ["hist", "histograma"]: sns.histplot(data=self.df, x=x, kde=True, hue=hue)
            
            plt.title(titulo if titulo else tipo.title())
            plt.xlabel(x); plt.ylabel(y); plt.xticks(rotation=45)
            plt.tight_layout(); plt.show()
        except Exception as e:
            self._log("plot_err", e=str(e))
        return self

    def resumo_estatistico(self):
        self._log("stats")
        print(self.df.describe().T)
        self._log("types")
        print(self.df.dtypes)
        return self

    def salvar(self, caminho):
        try:
            if caminho.endswith('.csv'): self.df.to_csv(caminho, index=False)
            elif caminho.endswith('.xlsx'): self.df.to_excel(caminho, index=False)
            elif caminho.endswith('.parquet'): self.df.to_parquet(caminho)
            self._log("save", path=caminho)
        except Exception as e:
            print(f"Save Error: {e}")
        return self

    def pegar_dataframe(self):
        return self.df
    
    def selecionar_colunas(self, colunas):
        if isinstance(colunas, str): colunas = [colunas]
        cols_existentes = [c for c in colunas if c in self.df.columns]

        if len(cols_existentes) < len(colunas):
            faltantes = set(colunas) - set(cols_existentes)
            self._log("select_warn", cols=faltantes)

        self.df = self.df[cols_existentes]
        self._log("select_ok", n=len(cols_existentes))
        return self

    def transformar(self, colunas, regra):
        if isinstance(colunas, str): colunas = [colunas]
        
        r = regra.upper()

        RULES_MONEY = ["BRL", "USD", "CNY", "INR", "DINHEIRO", "MONEY", "CURRENCY", "金钱", "PAISA", "MUDRA"]
        RULES_NUM   = ["CPF", "CNPJ", "NUMEROS", "NUMBERS", "TELEFONE", "DIGITS", "数字", "ANK"]
        RULES_EMAIL = ["EMAIL", "E-MAIL", "MAIL", "邮件"]
        RULES_UPPER = ["UPPER", "MAIUSCULO", "CAPS", "大写", "BADA"]
        RULES_LOWER = ["LOWER", "MINUSCULO", "XIAOXIE", "CHOTA"]
        
        for col in colunas:
            if col not in self.df.columns:
                continue

            if r in RULES_MONEY:
                moeda_a_usar = r if r in self.CURRENCY_MAP.values() else self.currency
                self.df[col] = self.df[col].apply(lambda x: self._tratar_moeda(x, moeda_a_usar))
                self._log("trans_money", col=col)

            elif r in RULES_NUM:
                self.df[col] = self.df[col].astype(str).str.replace(r'\D', '', regex=True)
                self._log("trans_num", col=col)

            elif r in RULES_EMAIL:
                self.df[col] = self.df[col].astype(str).str.lower().str.strip()
                mask = ~self.df[col].str.contains(r'[^@]+@[^@]+\.[^@]+', na=False)
                self.df.loc[mask, col] = np.nan
                self._log("trans_email", col=col)

            elif r in RULES_UPPER:
                self.df[col] = self.df[col].astype(str).str.upper()
            elif r in RULES_LOWER:
                self.df[col] = self.df[col].astype(str).str.lower()
            
            else:
                self._log("trans_err", rule=regra)
        
        return self

    def _tratar_moeda(self, valor, codigo_moeda):
        if pd.isna(valor): 
            return np.nan
        
        s = str(valor).strip()
        
        if codigo_moeda == "BRL":
            s = s.replace('R$', '').replace(' ', '').replace('.', '')
            s = s.replace(',', '.')
        elif codigo_moeda == "USD":
            s = s.replace('$', '').replace(' ', '').replace(',', '')
        elif codigo_moeda == "CNY":
            s = s.replace('¥', '').replace(' ', '').replace(',', '')
        elif codigo_moeda == "INR":
            s = s.replace('₹', '').replace(' ', '').replace(',', '')
        try:
            return float(s)
        except:
            return np.nan
        
    def agrupar(self, colunas_agrupar, coluna_valor, operacao="soma"):
        ops = {"soma": "sum", "media": "mean", "contagem": "count", "max": "max", "min": "min"}
        op_pandas = ops.get(operacao, "sum")
        try:
            resultado = self.df.groupby(colunas_agrupar)[coluna_valor].agg(op_pandas).reset_index()
            self._log("view", header=f"Agrupamento por {colunas_agrupar} ({operacao})")
            print(resultado)
        except Exception as e:
            print(f"Erro ao agrupar: {e}")
        return self

    def tabela_dinamica(self, indice, colunas, valores, func="soma"):
        ops = {"soma": "sum", "media": "mean", "contagem": "count"}
        try:
            pivot = pd.pivot_table(self.df, values=valores, index=indice, columns=colunas, aggfunc=ops.get(func, "sum"))
            self._log("view", header="Tabela Dinâmica")
            print(pivot)
        except Exception as e:
            print(f"Erro na Pivot Table: {e}")
        return self

    def exportar_mongo(self, uri, database, collection):
        try:
            import pymongo
            client = pymongo.MongoClient(uri)
            db = client[database]
            col = db[collection]
            dados = self.df.to_dict(orient="records")
            col.insert_many(dados)
            self._log("mongo_ok", col=collection)
            
        except ImportError:
            print("Erro: Instale o pymongo -> pip install pymongo")
        except Exception as e:
            self._log("save_err", e=str(e))
        return self

    def exportar_sql(self, url_conexao, nome_tabela, modo="append"):
        try:
            engine = create_engine(url_conexao)
            self.df.to_sql(nome_tabela, engine, if_exists=modo, index=False)
            self._log("sql_ok", tb=nome_tabela)
        except Exception as e:
            self._log("sql_err", e=str(e))
        return self

    def matriz_correlacao(self):
        try:
            plt.figure(figsize=(10, 8))
            df_num = self.df.select_dtypes(include=[np.number])
            corr = df_num.corr()
            sns.heatmap(corr, annot=True, cmap="coolwarm", fmt=".2f", linewidths=0.5)
            plt.title("Matriz de Correlação")
            plt.show()
        except Exception as e:
            self._log("plot_err", e=str(e))
        return self

    def tratar_outliers(self, colunas, metodo="iqr"):
        if isinstance(colunas, str): colunas = [colunas]
        antes = len(self.df)
        
        for col in colunas:
            Q1 = self.df[col].quantile(0.25)
            Q3 = self.df[col].quantile(0.75)
            IQR = Q3 - Q1
            filtro = ~((self.df[col] < (Q1 - 1.5 * IQR)) | (self.df[col] > (Q3 + 1.5 * IQR)))
            self.df = self.df[filtro]
            
        self._log("outlier_rem", qtd=antes - len(self.df))
        return self

    def escalonar(self, metodo="minmax"):
        cols_num = self.df.select_dtypes(include=[np.number]).columns
                
        if metodo == "minmax":
            self.scaler = MinMaxScaler()
        else:
            self.scaler = StandardScaler()
            
        self.df[cols_num] = self.scaler.fit_transform(self.df[cols_num])
        self._log("scale_ok", method=metodo)
        return self
    
    def auto_ml(self, **kwargs):
        alvo = kwargs.get('alvo') or kwargs.get('target') or kwargs.get('mubiao')
        raw_tipo = kwargs.get('tipo') or kwargs.get('type') or "classificacao"
        teste_tam = kwargs.get('teste_tam') or kwargs.get('test_size') or 0.2
        salvar_modelo = kwargs.get('salvar_modelo') or kwargs.get('save_path')

        if not alvo:
            print("[ERRO] Target/Alvo not defined.")
            return self

        tipo_lower = str(raw_tipo).lower()
        eh_classificacao = any(x in tipo_lower for x in ['class', 'fenlei', 'binario'])
        
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import accuracy_score, r2_score
        from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, RandomForestRegressor, GradientBoostingRegressor
        from sklearn.linear_model import LogisticRegression, LinearRegression

        self._log("ml_start", target=alvo)

        try:
            df_ml = self.df.dropna()
            X = df_ml.drop(columns=[alvo])
            y = df_ml[alvo]
    
            cols_datas = X.select_dtypes(include=['datetime', 'datetimetz']).columns
            if len(cols_datas) > 0:
                X = X.drop(columns=cols_datas)

            X = pd.get_dummies(X, drop_first=True)
            self._log("ml_feats", n=X.shape[1])
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=teste_tam, random_state=42)
            
            if eh_classificacao:
                modelos = {
                    "LogisticRegression": LogisticRegression(max_iter=1000),
                    "RandomForest": RandomForestClassifier(n_estimators=100, random_state=42),
                    "GradientBoosting": GradientBoostingClassifier(random_state=42)
                }
                metrica_nome = "Acurácia"
            else:
                modelos = {
                    "LinearRegression": LinearRegression(),
                    "RandomForest": RandomForestRegressor(n_estimators=100, random_state=42),
                    "GradientBoosting": GradientBoostingRegressor(random_state=42)
                }
                metrica_nome = "R² Score"

            melhor_score = -float("inf")
            melhor_modelo = None
            melhor_nome = ""

            self._log("ml_tourn", n=len(modelos))
            
            for nome, modelo in modelos.items():
                try:
                    modelo.fit(X_train, y_train)
                    preds = modelo.predict(X_test)
                    
                    if eh_classificacao:
                        score = accuracy_score(y_test, preds)
                    else:
                        score = r2_score(y_test, preds)
                    
                    if score > melhor_score:
                        melhor_score = score
                        melhor_modelo = modelo
                        melhor_nome = nome
                        
                except Exception as e:
                    self._log("ml_fail", name=nome, e=str(e))

            self._log("ml_win", name=melhor_nome, metric=metrica_nome, score=melhor_score)
            
            if salvar_modelo:
                dados_ia = {
                    "modelo": melhor_modelo, 
                    "colunas_treino": X.columns.tolist(), 
                    "scaler": self.scaler,
                    "tipo_modelo": melhor_nome,
                    "score": melhor_score
                }
                joblib.dump(dados_ia, salvar_modelo)
                self._log("ml_saved", path=salvar_modelo)
                
        except Exception as e:
            print(f"AutoML Error: {e}")
            import traceback; traceback.print_exc()
            
        return self

    def carregar_ia(self, caminho_modelo):
        try:
            dados_ia = joblib.load(caminho_modelo)
            self.modelo_ativo = dados_ia["modelo"]
            self.colunas_treino = dados_ia["colunas_treino"]
            self.scaler = dados_ia.get("scaler")
            self._log("ia_loaded", n=len(self.colunas_treino))
        except Exception as e:
            print(f"Load AI Error: {e}")
        return self

    def prever(self, nome_coluna_saida="previsao"):
        if not hasattr(self, 'modelo_ativo'):
            print("Carregue a IA primeiro!")
            print(self.I18N.get(self.lang, self.I18N["en"])["err_load_ia"])
            return self

        try:
            df_temp = self.df.copy()
            cols_datas = df_temp.select_dtypes(include=['datetime', 'datetimetz']).columns
            if len(cols_datas) > 0: df_temp = df_temp.drop(columns=cols_datas)
            if self.scaler:
                cols_num = df_temp.select_dtypes(include=[np.number]).columns

                try:
                    df_temp[cols_num] = self.scaler.transform(df_temp[cols_num])
                except:
                    pass
                
            df_pronto = pd.get_dummies(df_temp, drop_first=True)
            df_pronto = df_pronto.reindex(columns=self.colunas_treino, fill_value=0)

            preds = self.modelo_ativo.predict(df_pronto)
            self.df[nome_coluna_saida] = preds
            self._log("pred_done", col=nome_coluna_saida)
        except Exception as e:
            print(f"Prediction Error: {e}")
        return self

    def servir_api(self):
        if not hasattr(self, 'modelo_ativo'):
            print("Erro: Carregue um modelo com .carregar_ia() antes de iniciar a API.")
            return

        try:
            import uvicorn
            from fastapi import FastAPI
            from pydantic import BaseModel
            
            app = FastAPI(title="Sanice API", description="API gerada automaticamente pelo Sanice")

            class DadosInput(dict):
                pass

            @app.get("/")
            def home():
                return {"status": "Sanice está online", "modelo": str(type(self.modelo_ativo))}

            @app.post("/predict")
            def predict(dados: dict):
                
                df_api = pd.DataFrame([dados])
                
                if self.scaler:
                    cols_num = df_api.select_dtypes(include=[np.number]).columns
                    try: df_api[cols_num] = self.scaler.transform(df_api[cols_num])
                    except: pass
                
                df_api = pd.get_dummies(df_api, drop_first=True)
                df_api = df_api.reindex(columns=self.colunas_treino, fill_value=0)
                
                prediction = self.modelo_ativo.predict(df_api)
                return {"predicao": prediction.tolist()[0]}

            self._log("api_start")
            uvicorn.run(app, host="127.0.0.1", port=8000)
            
        except ImportError:
            print("Instale as libs: pip install fastapi uvicorn")
        except Exception as e:
            print(f"Erro API: {e}")
    
def cli():
    import sys
    
    VERSION = "1.0.9"

    CLI_MSGS = {
        "en": "To use inside Python:",
        "pt": "Para usar no script Python:",
        "zh": "在 Python 脚本中使用：",
        "hi": "Python script mein use karne ke liye:"
    }

    CMD_MAP = {
        "help": "en",
        "--help": "en",
        "-h": "en",
        "ajuda": "pt",
        "socorro": "pt",
        "bangzhu": "zh",
        "madad": "hi"
    }

    args = sys.argv
    comando = args[1].lower() if len(args) > 1 else ""

    if comando in ["-v", "--version", "version", "versao", "-version"]:
        print(f"Sanice v{VERSION}")
        return

    if comando in CMD_MAP:
        
        lang_padrao = CMD_MAP[comando]
        user_lang = args[2] if len(args) > 2 else lang_padrao
        
        if user_lang not in CLI_MSGS: user_lang = "en"
        msg = CLI_MSGS[user_lang]

        print(f"\n=== Sanice CLI Help ({user_lang.upper()}) ===")
        print(f"\n{msg}")
        print(f"  from sanice import Sanice")
        print(f"  app = Sanice('data.csv', lang='{user_lang}')")
        print(f"\nReference / Referência (PT | EN | ZH | HI):")
        print("-" * 75)
        
        for pt_method, aliases in Sanice.METHOD_ALIASES.items():
            en, zh, hi = aliases[0], aliases[1], aliases[2]
            print(f"  {pt_method:<20} | {en:<18} | {zh:<8} | {hi}")
            
        print("-" * 75)
        print(f"v{VERSION}")

    else:
        print(f"Sanice v{VERSION} installed! Try:")
        print("  sanice help     (English)")
        print("  sanice ajuda    (Português)")
        print("  sanice --version")