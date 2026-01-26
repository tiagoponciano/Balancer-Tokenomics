import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Prevent this file from being rendered as a Streamlit page
# This is a utility module, not a page - it should only be imported
# Check if this is being run as a page (has page config or is being accessed directly)
try:
    # If this file is accessed as a page, show a message and stop
    if hasattr(st, '_is_running_with_streamlit') and st._is_running_with_streamlit:
        # Check if we're in the main execution context (not imported)
        import inspect
        frame = inspect.currentframe()
        # If called directly (not imported), show message
        if frame and frame.f_back and 'streamlit' in str(frame.f_back.f_code.co_filename):
            st.info("ℹ️ **utils.py** is a utility module, not a page.\n\nPlease use the pages from the sidebar menu: Home, Bribes Analysis, Pool Classification, etc.")
            st.stop()
except:
    pass

def inject_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        /* --- ESTRUTURA GERAL --- */
        .stApp {
            background: linear-gradient(135deg, #0F1419 0%, #1A1F26 100%);
            font-family: 'Inter', sans-serif;
        }
        
        .block-container {
            padding-top: 3rem;
            padding-bottom: 2rem;
            max-width: 1400px;
        }
        
        h1, h2, h3, h4, h5, h6 {
            font-family: 'Inter', sans-serif;
            font-weight: 600;
            letter-spacing: -0.02em;
            color: #FFFFFF;
        }
        
        .page-title {
            font-size: 2.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, #67A2E1 0%, #B1ACF1 50%, #E9A97B 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 0.5rem;
            letter-spacing: -0.03em;
            position: relative;
            display: inline-block;
        }
        
        .page-title::before {
            content: '';
            position: absolute;
            left: 50%;
            top: 50%;
            transform: translate(-50%, -50%);
            width: 800px;
            height: 800px;
            background: radial-gradient(circle, rgba(255, 255, 255, 0.04) 0%, rgba(255, 255, 255, 0.02) 30%, transparent 60%);
            border-radius: 50%;
            filter: blur(80px);
            mix-blend-mode: overlay;
            pointer-events: none;
            z-index: -1;
        }
        
        .page-subtitle {
            font-size: 1rem;
            color: #8B95A6;
            font-weight: 400;
            margin-bottom: 2rem;
        }
        
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #1A1F26 0%, #151A20 100%);
            border-right: 1px solid rgba(255, 255, 255, 0.08);
        }
        
        div[data-testid="metric-container"] {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            padding: 1.5rem;
            backdrop-filter: blur(10px);
        }
        
        div[data-testid="metric-container"] label {
            color: #8B95A6 !important;
            font-size: 0.875rem;
            font-weight: 500;
        }
        
        div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
            color: #FFFFFF !important;
            font-size: 1.75rem;
            font-weight: 700;
        }
        
        div[data-testid="metric-container"] div[data-testid="stMetricDelta"] {
            font-weight: 500;
        }
        
        .stSlider {
            position: relative;
        }
        
        .stSlider::before {
            content: '';
            position: absolute;
            left: 50%;
            top: 50%;
            transform: translate(-50%, -50%);
            width: 800px;
            height: 800px;
            background: radial-gradient(circle, rgba(255, 255, 255, 0.04) 0%, rgba(255, 255, 255, 0.02) 30%, transparent 60%);
            border-radius: 50%;
            filter: blur(80px);
            mix-blend-mode: overlay;
            pointer-events: none;
            z-index: -1;
        }
        
        .stSlider > div > div > div[role="slider"] {
            background-color: #67A2E1 !important;
        }
        
        .stSlider > div > div > div > div {
            background-color: #FF4B4B !important;
        }
        
        hr {
            border: none;
            height: 1px;
            background: linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.1) 50%, transparent 100%);
            margin: 2rem 0;
        }
        
        section[data-testid="stSidebar"] hr {
            margin: 0.4rem 0 !important;
        }
        
        .stInfo {
            background: rgba(103, 162, 225, 0.1);
            border: 1px solid rgba(103, 162, 225, 0.2);
            border-radius: 8px;
        }
        
        .stCaption {
            color: #6B7280;
            font-size: 0.8125rem;
        }
        
        /* --- BOTÕES PADRÃO (fallback para outros botões) --- */
        /* Exclui explicitamente os botões com IDs específicos (genéricos e específicos) */
        .stButton > button:not([id^="btn_top20"]):not([id^="btn_worst20"]):not([id^="btn_select_all"]):not(#btn_performance_by_pool):not([id^="btn_login"]):not([id^="btn_logout"]):not(.logout-button):not([key="logout_btn"]):not([key="login_btn"]) {
            width: 110px;
            background-color: rgba(103, 162, 225, 0.1);
            border: 1px solid rgba(103, 162, 225, 0.3);
            color: #67A2E1;
            font-weight: 500;
            border-radius: 8px;
            padding: 0.5rem 1rem;
            position: relative;
            overflow: visible;
        }
        
        .stButton > button:not([id^="btn_top20"]):not([id^="btn_worst20"]):not([id^="btn_select_all"]):not(#btn_performance_by_pool):not([id^="btn_login"]):not([id^="btn_logout"]):not(.logout-button):not([key="logout_btn"]):not([key="login_btn"]):hover {
            background-color: rgba(103, 162, 225, 0.2);
            border-color: rgba(103, 162, 225, 0.5);
        }
        
        /* --- BOTÃO TOP 20 (genérico para todas as páginas) --- */
        button[id^="btn_top20"],
        [id^="btn_top20"] {
            width: 110px !important;
            min-width: 110px !important;
            max-width: 110px !important;
            height: 44px !important;
            padding: 0.625rem 0.5rem !important;
            font-size: 0.8125rem !important;
            font-weight: 600 !important;
            background: linear-gradient(135deg, rgba(103, 162, 225, 0.18) 0%, rgba(103, 162, 225, 0.08) 100%) !important;
            border: 1.5px solid rgba(103, 162, 225, 0.45) !important;
            color: #8BB5F0 !important;
            border-radius: 12px !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            box-shadow: 0 3px 12px rgba(103, 162, 225, 0.15) !important;
            position: relative !important;
            overflow: hidden !important;
            letter-spacing: 0.03em !important;
        }
        
        button[id^="btn_top20"]::before,
        [id^="btn_top20"]::before {
            content: '' !important;
            position: absolute !important;
            top: 0 !important;
            left: -100% !important;
            width: 100% !important;
            height: 100% !important;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.15), transparent) !important;
            transition: left 0.6s ease !important;
        }
        
        button[id^="btn_top20"]::after,
        [id^="btn_top20"]::after {
            content: '' !important;
            position: absolute !important;
            inset: 0 !important;
            border-radius: 12px !important;
            padding: 1.5px !important;
            background: linear-gradient(135deg, rgba(103, 162, 225, 0.6), rgba(103, 162, 225, 0.2)) !important;
            -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0) !important;
            -webkit-mask-composite: xor !important;
            mask-composite: exclude !important;
            opacity: 0 !important;
            transition: opacity 0.3s !important;
        }
        
        button[id^="btn_top20"]:hover,
        [id^="btn_top20"]:hover {
            background: linear-gradient(135deg, rgba(103, 162, 225, 0.28) 0%, rgba(103, 162, 225, 0.15) 100%) !important;
            border-color: rgba(103, 162, 225, 0.7) !important;
            transform: translateY(-3px) scale(1.02) !important;
            box-shadow: 0 6px 20px rgba(103, 162, 225, 0.3) !important;
            color: #A8C8F5 !important;
        }
        
        button[id^="btn_top20"]:hover::before,
        [id^="btn_top20"]:hover::before {
            left: 100% !important;
        }
        
        button[id^="btn_top20"]:hover::after,
        [id^="btn_top20"]:hover::after {
            opacity: 1 !important;
        }
        
        button[id^="btn_top20"]:active,
        [id^="btn_top20"]:active {
            transform: translateY(-1px) scale(1.01) !important;
            box-shadow: 0 3px 12px rgba(103, 162, 225, 0.2) !important;
        }
        
        /* --- BOTÃO WORST 20 (genérico para todas as páginas) --- */
        button[id^="btn_worst20"],
        [id^="btn_worst20"] {
            width: 110px !important;
            min-width: 110px !important;
            max-width: 110px !important;
            height: 44px !important;
            padding: 0.625rem 0.5rem !important;
            font-size: 0.8125rem !important;
            font-weight: 600 !important;
            background: linear-gradient(135deg, rgba(103, 162, 225, 0.18) 0%, rgba(103, 162, 225, 0.08) 100%) !important;
            border: 1.5px solid rgba(103, 162, 225, 0.45) !important;
            color: #8BB5F0 !important;
            border-radius: 12px !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            box-shadow: 0 3px 12px rgba(103, 162, 225, 0.15) !important;
            position: relative !important;
            overflow: hidden !important;
            letter-spacing: 0.03em !important;
        }
        
        button[id^="btn_worst20"]::before,
        [id^="btn_worst20"]::before {
            content: '' !important;
            position: absolute !important;
            top: 0 !important;
            left: -100% !important;
            width: 100% !important;
            height: 100% !important;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.15), transparent) !important;
            transition: left 0.6s ease !important;
        }
        
        button[id^="btn_worst20"]::after,
        [id^="btn_worst20"]::after {
            content: '' !important;
            position: absolute !important;
            inset: 0 !important;
            border-radius: 12px !important;
            padding: 1.5px !important;
            background: linear-gradient(135deg, rgba(103, 162, 225, 0.6), rgba(103, 162, 225, 0.2)) !important;
            -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0) !important;
            -webkit-mask-composite: xor !important;
            mask-composite: exclude !important;
            opacity: 0 !important;
            transition: opacity 0.3s !important;
        }
        
        button[id^="btn_worst20"]:hover,
        [id^="btn_worst20"]:hover {
            background: linear-gradient(135deg, rgba(103, 162, 225, 0.28) 0%, rgba(103, 162, 225, 0.15) 100%) !important;
            border-color: rgba(103, 162, 225, 0.7) !important;
            transform: translateY(-3px) scale(1.02) !important;
            box-shadow: 0 6px 20px rgba(103, 162, 225, 0.3) !important;
            color: #A8C8F5 !important;
        }
        
        button[id^="btn_worst20"]:hover::before,
        [id^="btn_worst20"]:hover::before {
            left: 100% !important;
        }
        
        button[id^="btn_worst20"]:hover::after,
        [id^="btn_worst20"]:hover::after {
            opacity: 1 !important;
        }
        
        button[id^="btn_worst20"]:active,
        [id^="btn_worst20"]:active {
            transform: translateY(-1px) scale(1.01) !important;
            box-shadow: 0 3px 12px rgba(103, 162, 225, 0.2) !important;
        }
        
        /* --- BOTÃO SELECT ALL (genérico para todas as páginas) --- */
        button[id^="btn_select_all"],
        [id^="btn_select_all"] {
            width: 110px !important;
            min-width: 110px !important;
            max-width: 110px !important;
            height: 44px !important;
            padding: 0.625rem 0.5rem !important;
            font-size: 0.8125rem !important;
            font-weight: 600 !important;
            background: linear-gradient(135deg, rgba(103, 162, 225, 0.18) 0%, rgba(103, 162, 225, 0.08) 100%) !important;
            border: 1.5px solid rgba(103, 162, 225, 0.45) !important;
            color: #8BB5F0 !important;
            border-radius: 12px !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            box-shadow: 0 3px 12px rgba(103, 162, 225, 0.15) !important;
            position: relative !important;
            overflow: hidden !important;
            letter-spacing: 0.03em !important;
        }
        
        button[id^="btn_select_all"]::before,
        [id^="btn_select_all"]::before {
            content: '' !important;
            position: absolute !important;
            top: 0 !important;
            left: -100% !important;
            width: 100% !important;
            height: 100% !important;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.15), transparent) !important;
            transition: left 0.6s ease !important;
        }
        
        button[id^="btn_select_all"]::after,
        [id^="btn_select_all"]::after {
            content: '' !important;
            position: absolute !important;
            inset: 0 !important;
            border-radius: 12px !important;
            padding: 1.5px !important;
            background: linear-gradient(135deg, rgba(103, 162, 225, 0.6), rgba(103, 162, 225, 0.2)) !important;
            -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0) !important;
            -webkit-mask-composite: xor !important;
            mask-composite: exclude !important;
            opacity: 0 !important;
            transition: opacity 0.3s !important;
        }
        
        button[id^="btn_select_all"]:hover,
        [id^="btn_select_all"]:hover {
            background: linear-gradient(135deg, rgba(103, 162, 225, 0.28) 0%, rgba(103, 162, 225, 0.15) 100%) !important;
            border-color: rgba(103, 162, 225, 0.7) !important;
            transform: translateY(-3px) scale(1.02) !important;
            box-shadow: 0 6px 20px rgba(103, 162, 225, 0.3) !important;
            color: #A8C8F5 !important;
        }
        
        button[id^="btn_select_all"]:hover::before,
        [id^="btn_select_all"]:hover::before {
            left: 100% !important;
        }
        
        button[id^="btn_select_all"]:hover::after,
        [id^="btn_select_all"]:hover::after {
            opacity: 1 !important;
        }
        
        button[id^="btn_select_all"]:active,
        [id^="btn_select_all"]:active {
            transform: translateY(-1px) scale(1.01) !important;
            box-shadow: 0 3px 12px rgba(103, 162, 225, 0.2) !important;
        }
        
        /* --- BOTÃO SHOW PERFORMANCE BY POOL --- */
        /* Seletor usando atributo data customizado (mais confiável) */
        button[data-button-type="performance"],
        button[data-testid="stBaseButton-secondary"][data-button-type="performance"] {
            width: 250px !important;
            max-width: 250px !important;
            min-width: 250px !important;
            height: 56px !important;
            padding: 0.625rem 1.5rem !important;
            font-weight: 600 !important;
            background: linear-gradient(135deg, rgba(103, 162, 225, 0.18) 0%, rgba(103, 162, 225, 0.08) 100%) !important;
            border: 1.5px solid rgba(103, 162, 225, 0.45) !important;
            color: #8BB5F0 !important;
            border-radius: 12px !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            box-shadow: 0 3px 12px rgba(103, 162, 225, 0.15) !important;
            position: relative !important;
            overflow: hidden !important;
            letter-spacing: 0.02em !important;
        }
        
        /* Classe de fallback aplicada via JavaScript */
        button.performance-button-fallback,
        button[data-testid="stBaseButton-secondary"].performance-button-fallback,
        button[data-testid="stBaseButton-primary"].performance-button-fallback {
            width: 250px !important;
            max-width: 250px !important;
            min-width: 250px !important;
            height: 56px !important;
            padding: 0.625rem 1.5rem !important;
            font-weight: 600 !important;
            background: linear-gradient(135deg, rgba(103, 162, 225, 0.18) 0%, rgba(103, 162, 225, 0.08) 100%) !important;
            border: 1.5px solid rgba(103, 162, 225, 0.45) !important;
            color: #8BB5F0 !important;
            border-radius: 12px !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            box-shadow: 0 3px 12px rgba(103, 162, 225, 0.15) !important;
            position: relative !important;
            overflow: hidden !important;
            letter-spacing: 0.02em !important;
        }
        
        /* Múltiplos seletores com alta especificidade para garantir prioridade */
        /* Ordem: do mais específico ao menos específico */
        button[data-testid="stBaseButton-secondary"]#btn_performance_by_pool,
        button[data-testid="stBaseButton-primary"]#btn_performance_by_pool,
        button[data-testid*="stBaseButton"]#btn_performance_by_pool,
        .stButton > button#btn_performance_by_pool,
        div[data-testid="stButton"] > button#btn_performance_by_pool,
        button#btn_performance_by_pool,
        #btn_performance_by_pool {
            /* width precisa de !important porque pode ser sobrescrito por estilos inline do Streamlit */
            width: 250px !important;
            max-width: 250px !important;
            min-width: 250px !important;
            height: 56px !important;
            padding: 0.625rem 1.5rem !important;
            font-weight: 600 !important;
            background: linear-gradient(135deg, rgba(103, 162, 225, 0.18) 0%, rgba(103, 162, 225, 0.08) 100%) !important;
            border: 1.5px solid rgba(103, 162, 225, 0.45) !important;
            color: #8BB5F0 !important;
            border-radius: 12px !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            box-shadow: 0 3px 12px rgba(103, 162, 225, 0.15) !important;
            position: relative !important;
            overflow: hidden !important;
            letter-spacing: 0.02em !important;
        }
        
        /* Pseudo-elements para o botão de performance (atributo data) */
        button[data-button-type="performance"]::before,
        button[data-testid="stBaseButton-secondary"][data-button-type="performance"]::before {
            content: '' !important;
            position: absolute !important;
            top: 0 !important;
            left: -100% !important;
            width: 100% !important;
            height: 100% !important;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.15), transparent) !important;
            transition: left 0.6s ease !important;
        }
        
        button[data-button-type="performance"]::after,
        button[data-testid="stBaseButton-secondary"][data-button-type="performance"]::after {
            content: '' !important;
            position: absolute !important;
            inset: 0 !important;
            border-radius: 12px !important;
            padding: 1.5px !important;
            background: linear-gradient(135deg, rgba(103, 162, 225, 0.6), rgba(103, 162, 225, 0.2)) !important;
            -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0) !important;
            -webkit-mask-composite: xor !important;
            mask-composite: exclude !important;
            opacity: 0 !important;
            transition: opacity 0.3s !important;
        }
        
        button[data-button-type="performance"]:hover,
        button[data-testid="stBaseButton-secondary"][data-button-type="performance"]:hover {
            background: linear-gradient(135deg, rgba(103, 162, 225, 0.28) 0%, rgba(103, 162, 225, 0.15) 100%) !important;
            border-color: rgba(103, 162, 225, 0.7) !important;
            transform: translateY(-3px) scale(1.02) !important;
            box-shadow: 0 6px 20px rgba(103, 162, 225, 0.3) !important;
            color: #A8C8F5 !important;
        }
        
        button[data-button-type="performance"]:hover::before,
        button[data-testid="stBaseButton-secondary"][data-button-type="performance"]:hover::before {
            left: 100% !important;
        }
        
        button[data-button-type="performance"]:hover::after,
        button[data-testid="stBaseButton-secondary"][data-button-type="performance"]:hover::after {
            opacity: 1 !important;
        }
        
        button[data-button-type="performance"]:active,
        button[data-testid="stBaseButton-secondary"][data-button-type="performance"]:active {
            transform: translateY(-1px) scale(1.01) !important;
            box-shadow: 0 3px 12px rgba(103, 162, 225, 0.2) !important;
        }
        
        /* Pseudo-elements para o botão de performance (classe de fallback) */
        button.performance-button-fallback::before {
            content: '' !important;
            position: absolute !important;
            top: 0 !important;
            left: -100% !important;
            width: 100% !important;
            height: 100% !important;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.15), transparent) !important;
            transition: left 0.6s ease !important;
        }
        
        button.performance-button-fallback::after {
            content: '' !important;
            position: absolute !important;
            inset: 0 !important;
            border-radius: 12px !important;
            padding: 1.5px !important;
            background: linear-gradient(135deg, rgba(103, 162, 225, 0.6), rgba(103, 162, 225, 0.2)) !important;
            -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0) !important;
            -webkit-mask-composite: xor !important;
            mask-composite: exclude !important;
            opacity: 0 !important;
            transition: opacity 0.3s !important;
        }
        
        button.performance-button-fallback:hover {
            background: linear-gradient(135deg, rgba(103, 162, 225, 0.28) 0%, rgba(103, 162, 225, 0.15) 100%) !important;
            border-color: rgba(103, 162, 225, 0.7) !important;
            transform: translateY(-3px) scale(1.02) !important;
            box-shadow: 0 6px 20px rgba(103, 162, 225, 0.3) !important;
            color: #A8C8F5 !important;
        }
        
        button.performance-button-fallback:hover::before {
            left: 100% !important;
        }
        
        button.performance-button-fallback:hover::after {
            opacity: 1 !important;
        }
        
        button.performance-button-fallback:active {
            transform: translateY(-1px) scale(1.01) !important;
            box-shadow: 0 3px 12px rgba(103, 162, 225, 0.2) !important;
        }
        
        /* Pseudo-elements para o botão de performance (ID) */
        #btn_performance_by_pool::before,
        button#btn_performance_by_pool::before {
            content: '' !important;
            position: absolute !important;
            top: 0 !important;
            left: -100% !important;
            width: 100% !important;
            height: 100% !important;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.15), transparent) !important;
            transition: left 0.6s ease !important;
        }
        
        #btn_performance_by_pool::after,
        button#btn_performance_by_pool::after {
            content: '' !important;
            position: absolute !important;
            inset: 0 !important;
            border-radius: 12px !important;
            padding: 1.5px !important;
            background: linear-gradient(135deg, rgba(103, 162, 225, 0.6), rgba(103, 162, 225, 0.2)) !important;
            -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0) !important;
            -webkit-mask-composite: xor !important;
            mask-composite: exclude !important;
            opacity: 0 !important;
            transition: opacity 0.3s !important;
        }
        
        #btn_performance_by_pool:hover,
        button#btn_performance_by_pool:hover {
            background: linear-gradient(135deg, rgba(103, 162, 225, 0.28) 0%, rgba(103, 162, 225, 0.15) 100%) !important;
            border-color: rgba(103, 162, 225, 0.7) !important;
            transform: translateY(-3px) scale(1.02) !important;
            box-shadow: 0 6px 20px rgba(103, 162, 225, 0.3) !important;
            color: #A8C8F5 !important;
        }
        
        #btn_performance_by_pool:hover::before,
        button#btn_performance_by_pool:hover::before {
            left: 100% !important;
        }
        
        #btn_performance_by_pool:hover::after,
        button#btn_performance_by_pool:hover::after {
            opacity: 1 !important;
        }
        
        #btn_performance_by_pool:active,
        button#btn_performance_by_pool:active {
            transform: translateY(-1px) scale(1.01) !important;
            box-shadow: 0 3px 12px rgba(103, 162, 225, 0.2) !important;
        }
        
        /* Seletor adicional com máxima especificidade para garantir que o botão de performance nunca receba o estilo padrão */
        button[data-testid="stBaseButton-secondary"]#btn_performance_by_pool.st-emotion-cache-1anq8dj,
        button[data-testid="stBaseButton-primary"]#btn_performance_by_pool.st-emotion-cache-1anq8dj,
        button[data-testid*="stBaseButton"]#btn_performance_by_pool[class*="st-emotion"] {
            width: 250px !important;
            min-width: 250px !important;
            max-width: 250px !important;
            height: 56px !important;
        }

        /* --- BOTÃO LOGIN --- */
        button[id^="btn_login"],
        [id^="btn_login"],
        button[key="login_btn"],
        form button[type="submit"] {
            width: 110px !important;
            min-width: 110px !important;
            max-width: 110px !important;
            height: 44px !important;
            padding: 0.625rem 0.5rem !important;
            font-size: 0.8125rem !important;
            font-weight: 600 !important;
            background: linear-gradient(135deg, rgba(103, 162, 225, 0.18) 0%, rgba(103, 162, 225, 0.08) 100%) !important;
            border: 1.5px solid rgba(103, 162, 225, 0.45) !important;
            color: #8BB5F0 !important;
            border-radius: 12px !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            box-shadow: 0 3px 12px rgba(103, 162, 225, 0.15) !important;
            position: relative !important;
            overflow: hidden !important;
            letter-spacing: 0.03em !important;
        }
        
        button[id^="btn_login"]::before,
        [id^="btn_login"]::before,
        button[key="login_btn"]::before,
        form button[type="submit"]::before {
            content: '' !important;
            position: absolute !important;
            top: 0 !important;
            left: -100% !important;
            width: 100% !important;
            height: 100% !important;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.15), transparent) !important;
            transition: left 0.6s ease !important;
        }
        
        button[id^="btn_login"]::after,
        [id^="btn_login"]::after,
        button[key="login_btn"]::after,
        form button[type="submit"]::after {
            content: '' !important;
            position: absolute !important;
            inset: 0 !important;
            border-radius: 12px !important;
            padding: 1.5px !important;
            background: linear-gradient(135deg, rgba(103, 162, 225, 0.6), rgba(103, 162, 225, 0.2)) !important;
            -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0) !important;
            -webkit-mask-composite: xor !important;
            mask-composite: exclude !important;
            opacity: 0 !important;
            transition: opacity 0.3s !important;
        }
        
        button[id^="btn_login"]:hover,
        [id^="btn_login"]:hover,
        button[key="login_btn"]:hover,
        form button[type="submit"]:hover {
            background: linear-gradient(135deg, rgba(103, 162, 225, 0.28) 0%, rgba(103, 162, 225, 0.15) 100%) !important;
            border-color: rgba(103, 162, 225, 0.7) !important;
            transform: translateY(-3px) scale(1.02) !important;
            box-shadow: 0 6px 20px rgba(103, 162, 225, 0.3) !important;
            color: #A8C8F5 !important;
        }
        
        button[id^="btn_login"]:hover::before,
        [id^="btn_login"]:hover::before,
        button[key="login_btn"]:hover::before,
        form button[type="submit"]:hover::before {
            left: 100% !important;
        }
        
        button[id^="btn_login"]:hover::after,
        [id^="btn_login"]:hover::after,
        button[key="login_btn"]:hover::after,
        form button[type="submit"]:hover::after {
            opacity: 1 !important;
        }
        
        button[id^="btn_login"]:active,
        [id^="btn_login"]:active,
        button[key="login_btn"]:active,
        form button[type="submit"]:active {
            transform: translateY(-1px) scale(1.01) !important;
            box-shadow: 0 3px 12px rgba(103, 162, 225, 0.2) !important;
        }
        
        /* --- BOTÃO LOGOUT --- */
        button[id^="btn_logout"],
        [id^="btn_logout"],
        button[key="logout_btn"] {
            width: 110px !important;
            min-width: 110px !important;
            max-width: 110px !important;
            height: 44px !important;
            padding: 0.625rem 0.5rem !important;
            font-size: 0.8125rem !important;
            font-weight: 600 !important;
            background: linear-gradient(135deg, rgba(103, 162, 225, 0.18) 0%, rgba(103, 162, 225, 0.08) 100%) !important;
            border: 1.5px solid rgba(103, 162, 225, 0.45) !important;
            color: #8BB5F0 !important;
            border-radius: 12px !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            box-shadow: 0 3px 12px rgba(103, 162, 225, 0.15) !important;
            position: relative !important;
            overflow: hidden !important;
            letter-spacing: 0.03em !important;
        }
        
        button[id^="btn_logout"]::before,
        [id^="btn_logout"]::before,
        button[key="logout_btn"]::before {
            content: '' !important;
            position: absolute !important;
            top: 0 !important;
            left: -100% !important;
            width: 100% !important;
            height: 100% !important;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.15), transparent) !important;
            transition: left 0.6s ease !important;
        }
        
        button[id^="btn_logout"]::after,
        [id^="btn_logout"]::after,
        button[key="logout_btn"]::after {
            content: '' !important;
            position: absolute !important;
            inset: 0 !important;
            border-radius: 12px !important;
            padding: 1.5px !important;
            background: linear-gradient(135deg, rgba(103, 162, 225, 0.6), rgba(103, 162, 225, 0.2)) !important;
            -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0) !important;
            -webkit-mask-composite: xor !important;
            mask-composite: exclude !important;
            opacity: 0 !important;
            transition: opacity 0.3s !important;
        }
        
        button[id^="btn_logout"]:hover,
        [id^="btn_logout"]:hover,
        button[key="logout_btn"]:hover {
            background: linear-gradient(135deg, rgba(103, 162, 225, 0.28) 0%, rgba(103, 162, 225, 0.15) 100%) !important;
            border-color: rgba(103, 162, 225, 0.7) !important;
            transform: translateY(-3px) scale(1.02) !important;
            box-shadow: 0 6px 20px rgba(103, 162, 225, 0.3) !important;
            color: #A8C8F5 !important;
        }
        
        button[id^="btn_logout"]:hover::before,
        [id^="btn_logout"]:hover::before,
        button[key="logout_btn"]:hover::before {
            left: 100% !important;
        }
        
        button[id^="btn_logout"]:hover::after,
        [id^="btn_logout"]:hover::after,
        button[key="logout_btn"]:hover::after {
            opacity: 1 !important;
        }
        
        button[id^="btn_logout"]:active,
        [id^="btn_logout"]:active,
        button[key="logout_btn"]:active {
            transform: translateY(-1px) scale(1.01) !important;
            box-shadow: 0 3px 12px rgba(103, 162, 225, 0.2) !important;
        }
        
        /* --- MULTISELECT STYLING (BASEWEB) --- */
        div[data-baseweb="select"] {
            position: relative;
        }
        
        /* Main select container */
        div[data-baseweb="select"] > div:first-child {
            background-color: rgba(103, 162, 225, 0.1) !important;
            border: 1px solid rgba(103, 162, 225, 0.3) !important;
            border-radius: 8px !important;
            padding: 0.5rem 1rem !important;
            min-height: 40px !important;
            max-height: 120px !important;
            font-size: 1rem !important;
            font-weight: 500 !important;
            color: white !important;
            transition: all 0.2s !important;
            display: flex !important;
            align-items: flex-start !important;
            justify-content: flex-start !important;
            gap: 0.5rem !important;
            overflow-y: auto !important;
            overflow-x: hidden !important;
        }
        
        div[data-baseweb="select"] > div:first-child:hover {
            background-color: rgba(103, 162, 225, 0.2) !important;
            border-color: rgba(103, 162, 225, 0.5) !important;
        }
        
        div[data-baseweb="select"] > div:first-child:focus,
        div[data-baseweb="select"] > div:first-child:focus-within {
            outline: none !important;
            box-shadow: 0 0 0 3px rgba(103, 162, 225, 0.3) !important;
        }
        
        /* Selected values display - scrollable container */
        div[data-baseweb="select"] span[role="listbox"] {
            display: flex !important;
            flex-wrap: wrap !important;
            gap: 0.25rem !important;
            width: 100% !important;
            align-items: flex-start !important;
        }
        
        /* Custom scrollbar for multiselect */
        div[data-baseweb="select"] > div:first-child::-webkit-scrollbar { width: 6px !important; }
        div[data-baseweb="select"] > div:first-child::-webkit-scrollbar-track {
            background: rgba(255, 255, 255, 0.1) !important; border-radius: 3px !important;
        }
        div[data-baseweb="select"] > div:first-child::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.3) !important; border-radius: 3px !important;
        }
        div[data-baseweb="select"] > div:first-child::-webkit-scrollbar-thumb:hover {
            background: rgba(255, 255, 255, 0.5) !important;
        }
        
        /* Multiselect tags/chips */
        div[data-baseweb="select"] span[role="listbox"] > span,
        div[data-baseweb="select"] span[role="listbox"] > div {
            background-color: #B1ACF1 !important;
            color: white !important;
            border-radius: 9999px !important;
            padding: 0.25rem 0.75rem !important;
            font-size: 0.875rem !important;
            display: inline-flex !important;
            align-items: center !important;
            gap: 0.5rem !important;
            margin: 0.125rem !important;
        }
        
        /* Placeholder text */
        div[data-baseweb="select"] div[data-baseweb="select"] > div > div[data-baseweb="select"] {
            color: rgba(255, 255, 255, 0.7) !important;
        }
        
        /* Input text color */
        div[data-baseweb="select"] input,
        div[data-baseweb="select"] div[data-baseweb="select"] input {
            color: white !important;
        }
        
        /* Multiselect dropdown */
        ul[role="listbox"],
        div[data-baseweb="popover"] {
            background-color: #1A1F26 !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 8px !important;
            padding: 0.5rem !important;
        }
        
        ul[role="listbox"] li, div[data-baseweb="popover"] li {
            color: white !important;
            padding: 0.5rem 0.75rem !important;
            border-radius: 4px !important;
        }
        
        ul[role="listbox"] li:hover, div[data-baseweb="popover"] li:hover {
            background-color: rgba(103, 162, 225, 0.1) !important;
        }
        
        ul[role="listbox"] li[aria-selected="true"], div[data-baseweb="popover"] li[aria-selected="true"] {
            background-color: rgba(103, 162, 225, 0.2) !important;
        }
        
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
    </style>
    <script>
        console.log('[Button IDs] Script do utils.py carregado!');
        
        // Script de fallback para aplicar classe ao botão de performance
        (function() {
            function applyPerformanceButtonClass() {
                const contexts = [
                    document,
                    window.parent?.document || document,
                    window.top?.document || document
                ];
                
                contexts.forEach((doc, ctxIndex) => {
                    if (!doc) return;
                    
                    const buttons = doc.querySelectorAll('button[data-testid*="stBaseButton"]');
                    
                    buttons.forEach((button, index) => {
                        // Tenta pegar o texto de múltiplas formas
                        let text = '';
                        try {
                            text = (button.textContent || button.innerText || '').trim();
                            if (!text || text.length === 0) {
                                const markdownEl = button.querySelector('[data-testid="stMarkdownContainer"]');
                                if (markdownEl) {
                                    text = (markdownEl.textContent || markdownEl.innerText || '').trim();
                                }
                            }
                            if (!text || text.length === 0) {
                                const pEl = button.querySelector('p');
                                if (pEl) {
                                    text = (pEl.textContent || pEl.innerText || '').trim();
                                }
                            }
                        } catch(e) {}
                        
                        const textLower = text.toLowerCase();
                        
                        // Detecta botões "Top 20", "Worst 20" e "Select All" em todas as páginas
                        // Aplica IDs que começam com os prefixos corretos para que o CSS funcione
                        if (text === 'Top 20' || textLower === 'top 20') {
                            // Garante que o ID comece com btn_top20
                            if (!button.id || !button.id.startsWith('btn_top20')) {
                                button.id = 'btn_top20';
                            }
                        } else if (text === 'Worst 20' || textLower === 'worst 20') {
                            if (!button.id || !button.id.startsWith('btn_worst20')) {
                                button.id = 'btn_worst20';
                            }
                        } else if (text === 'Select All' || textLower === 'select all') {
                            if (!button.id || !button.id.startsWith('btn_select_all')) {
                                button.id = 'btn_select_all';
                            }
                        } else if (text === 'Login' || textLower === 'login') {
                            // Botão de login
                            if (!button.id || !button.id.startsWith('btn_login')) {
                                button.id = 'btn_login';
                            }
                        } else if (text.includes('Logout') || text.includes('🚪') || textLower.includes('logout')) {
                            // Botão de logout
                            if (!button.id || !button.id.startsWith('btn_logout')) {
                                button.id = 'btn_logout';
                            }
                        } else if (text.includes('Show Performance') || text.includes('Performance by Pool') || textLower.includes('performance') || text.includes('🔍')) {
                            // Aplica ID se ainda não tiver
                            if (!button.id || button.id !== 'btn_performance_by_pool') {
                                button.id = 'btn_performance_by_pool';
                            }
                            // Aplica atributo data customizado
                            button.setAttribute('data-button-type', 'performance');
                            // Aplica classe de fallback
                            button.classList.add('performance-button-fallback');
                            
                            // Aplica TODOS os estilos inline diretamente (máxima prioridade)
                            const styles = {
                                'width': '250px',
                                'min-width': '250px',
                                'max-width': '250px',
                                'height': '56px',
                                'padding': '0.625rem 1.5rem',
                                'font-weight': '600',
                                'background': 'linear-gradient(135deg, rgba(103, 162, 225, 0.18) 0%, rgba(103, 162, 225, 0.08) 100%)',
                                'border': '1.5px solid rgba(103, 162, 225, 0.45)',
                                'color': '#8BB5F0',
                                'border-radius': '12px',
                                'transition': 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                                'box-shadow': '0 3px 12px rgba(103, 162, 225, 0.15)',
                                'position': 'relative',
                                'overflow': 'hidden',
                                'letter-spacing': '0.02em'
                            };
                            
                            Object.keys(styles).forEach(prop => {
                                button.style.setProperty(prop, styles[prop], 'important');
                            });
                            
                            console.log('[Button IDs] ✅ Botão performance estilizado via utils.py');
                        }
                    });
                });
            }
            
            // Executa imediatamente
            applyPerformanceButtonClass();
            
            // Executa após delays
            setTimeout(applyPerformanceButtonClass, 100);
            setTimeout(applyPerformanceButtonClass, 300);
            setTimeout(applyPerformanceButtonClass, 500);
            setTimeout(applyPerformanceButtonClass, 1000);
            
            // Executa repetidamente
            setInterval(applyPerformanceButtonClass, 2000);
            
            // Observa mudanças no DOM
            if (window.MutationObserver) {
                const observer = new MutationObserver(() => {
                    setTimeout(applyPerformanceButtonClass, 50);
                });
                
                const contexts = [
                    document,
                    window.parent?.document || document,
                    window.top?.document || document
                ];
                
                contexts.forEach(doc => {
                    if (doc && doc.body) {
                        observer.observe(doc.body, { childList: true, subtree: true });
                    }
                });
            }
        })();
    </script>
    """, unsafe_allow_html=True)

def check_authentication():
    """Check if user is authenticated, show login page if not"""
    # Credentials from environment variables (required)
    CORRECT_USERNAME = os.getenv("LOGIN_USERNAME")
    CORRECT_PASSWORD = os.getenv("LOGIN_PASSWORD")
    
    # Validate that credentials are set
    if not CORRECT_USERNAME or not CORRECT_PASSWORD:
        st.error("Authentication credentials not configured. Please set LOGIN_USERNAME and LOGIN_PASSWORD in your .env file.")
        st.stop()
        return False
    
    # Initialize authentication state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    # If already authenticated, allow access
    if st.session_state.authenticated:
        return True
    
    # Show login page
    st.markdown("""
    <style>
        .login-title {
            font-size: 2rem;
            font-weight: 700;
            background: linear-gradient(135deg, #67A2E1 0%, #B1ACF1 50%, #E9A97B 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-align: center;
            margin-bottom: 0.5rem;
        }
        .login-subtitle {
            color: #8B95A6;
            text-align: center;
            margin-bottom: 2rem;
            font-size: 0.9rem;
        }
        .stTextInput > div > div > input {
            background-color: rgba(26, 31, 38, 0.6) !important;
            border: 1px solid rgba(103, 162, 225, 0.3) !important;
            color: white !important;
            border-radius: 8px !important;
        }
        .stTextInput > div > div > input:focus {
            border-color: #67A2E1 !important;
            box-shadow: 0 0 0 3px rgba(103, 162, 225, 0.2) !important;
        }
        /* CSS do botão de login já está no inject_css() */
        /* Mantém apenas estilos específicos para outros botões na página de login se necessário */
    </style>
    """, unsafe_allow_html=True)
    
    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="login-title">🔐 Authentication Required</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-subtitle">Please enter your credentials to access the dashboard</div>', unsafe_allow_html=True)
        
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username", key="login_username")
            password = st.text_input("Password", type="password", placeholder="Enter your password", key="login_password")
            
            submitted = st.form_submit_button("Login", use_container_width=True, key="login_btn")
            
            if submitted:
                if username == CORRECT_USERNAME and password == CORRECT_PASSWORD:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("❌ Invalid username or password. Please try again.")
    
    # Hide sidebar and menu when showing login
    st.markdown("""
    <style>
        section[data-testid="stSidebar"] {
            display: none;
        }
        #MainMenu {
            visibility: hidden;
        }
    </style>
    """, unsafe_allow_html=True)
    
    return False

def show_logout_button():
    """Show logout button in top right corner"""
    # Create button (will be positioned in the column passed to this function)
    # CSS já está aplicado no inject_css()
    if st.button("🚪 Logout", key="logout_btn"):
        st.session_state.authenticated = False
        st.rerun()

@st.cache_data
def load_data():
    try:
        # Get current working directory (where streamlit is run from)
        cwd = os.getcwd()
        
        # Try to get script directory
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(script_dir)
        except:
            script_dir = cwd
            project_root = os.path.dirname(cwd) if os.path.basename(cwd) == 'script' else cwd
        
        # Build possible data directories
        possible_data_dirs = [
            os.path.join(project_root, 'data'),
            os.path.join(cwd, 'data'),
            os.path.join(cwd, '..', 'data'),
            os.path.join(script_dir, 'data'),
            'data'
        ]
        
        # Try different possible file names and paths
        # Priority: ../data/ (most likely when running from script/)
        file_paths = [
            os.path.abspath(os.path.join(cwd, '..', 'data', 'balancer_v2_financial_master_final.csv')),  # ../data/ - MOST LIKELY
        ]
        # Then try other data directories
        for data_dir in possible_data_dirs:
            abs_data_dir = os.path.abspath(data_dir)
            file_paths.extend([
                os.path.join(abs_data_dir, 'balancer_v2_financial_master_final.csv'),
                os.path.join(abs_data_dir, 'balancer_v2_best_pools.csv'),
            ])
        # Also try relative to current directory
        file_paths.extend([
            os.path.join(cwd, 'balancer_v2_financial_master_final.csv'),
            'data/balancer_v2_financial_master_final.csv',
            'balancer_v2_financial_master_final.csv'
        ])
        
        df = None
        found_path = None
        for path in file_paths:
            try:
                # Normalize path
                if not os.path.isabs(path):
                    abs_path = os.path.abspath(path)
                else:
                    abs_path = path
                
                # Check if file exists and has content
                if os.path.exists(abs_path) and os.path.getsize(abs_path) > 100:  # At least 100 bytes
                    df = pd.read_csv(abs_path)
                    if df is not None and not df.empty:
                        found_path = abs_path
                        break
            except (FileNotFoundError, pd.errors.EmptyDataError, pd.errors.ParserError, Exception) as e:
                continue
        
        if df is None or df.empty:
            error_msg = st.error("❌ CSV file not found or is empty.")
            with st.expander("🔍 Debug Info - Click to see details"):
                st.write(f"**Current working directory:** `{cwd}`")
                st.write(f"**Script directory:** `{script_dir}`")
                st.write(f"**Project root:** `{project_root}`")
                st.write("**Tried paths:**")
                for i, path in enumerate(file_paths[:15], 1):
                    abs_path = os.path.abspath(path)
                    exists = "✅" if os.path.exists(abs_path) else "❌"
                    st.write(f"{i}. {exists} `{abs_path}`")
                # List files in data directory if it exists
                for data_dir in possible_data_dirs:
                    abs_data_dir = os.path.abspath(data_dir)
                    if os.path.exists(abs_data_dir):
                        st.write(f"\n**Files in `{abs_data_dir}`:**")
                        try:
                            files = [f for f in os.listdir(abs_data_dir) if f.endswith('.csv')]
                            for f in files[:10]:
                                st.write(f"  - {f}")
                        except:
                            pass
            return pd.DataFrame()
        
        if 'block_date' in df.columns:
            df['block_date'] = pd.to_datetime(df['block_date'], errors='coerce')
        
        numeric_cols = [
            'protocol_fee_amount_usd',
            'total_protocol_fee_usd',
            'direct_incentives',
            'dao_profit_usd',
            'bal_emited_votes',
            'votes_received',
            'emissions_roi',
            'is_core_pool'
        ]
        
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        if 'is_core_pool' in df.columns:
            df['is_core_pool'] = df['is_core_pool'].astype(int)
        
        if 'pool_category' not in df.columns:
            df = classify_pools(df)
        
        return df
    
    except FileNotFoundError:
        st.error("❌ CSV file not found. Please verify that 'balancer_v2_financial_master_final.csv' is in the correct directory.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Error loading data: {str(e)}")
        return pd.DataFrame()

def classify_pools(df):
    pool_agg = df.groupby('pool_symbol').agg({
        'dao_profit_usd': 'sum',
        'protocol_fee_amount_usd': 'sum',
        'direct_incentives': 'sum',
        'emissions_roi': 'mean',
        'is_core_pool': 'max'
    }).reset_index()
    
    pool_agg.columns = ['pool_symbol', 'total_dao_profit', 'total_revenue', 'total_incentives', 'avg_roi', 'is_core_pool']
    
    pool_agg['incentive_dependency'] = np.where(
        pool_agg['total_revenue'] > 0,
        pool_agg['total_incentives'] / pool_agg['total_revenue'],
        1.0
    )
    
    def classify_pool(row):
        if row['total_incentives'] == 0:
            if row['total_revenue'] > 10000:
                return 'Legitimate'
            return 'Undefined'
        
        if row['total_revenue'] == 0:
            return 'Mercenary'
        
        if row['avg_roi'] < 0.5:
            return 'Mercenary'
        
        if row['total_dao_profit'] < -1000:
            return 'Mercenary'
        
        if row['incentive_dependency'] > 0.8:
            return 'Mercenary'
        
        if row['total_revenue'] < 10000:
            return 'Mercenary'
        
        if row['total_dao_profit'] > 0 and row['avg_roi'] > 1.0:
            return 'Legitimate'
        
        if row['is_core_pool'] == 1 and row['avg_roi'] > 0.7:
            return 'Legitimate'
        
        return 'Undefined'
    
    pool_agg['pool_category'] = pool_agg.apply(classify_pool, axis=1)
    
    df = df.merge(
        pool_agg[['pool_symbol', 'pool_category']],
        on='pool_symbol',
        how='left'
    )
    
    df['pool_category'] = df['pool_category'].fillna('Undefined')
    
    return df

@st.cache_data
def load_vebal_votes_data():
    """Load veBAL votes data"""
    try:
        cwd = os.getcwd()
        file_paths = [
            os.path.abspath(os.path.join(cwd, '..', 'data', 'veBAL_votes.csv')),
            os.path.abspath(os.path.join(cwd, 'data', 'veBAL_votes.csv')),
            'data/veBAL_votes.csv',
            'veBAL_votes.csv'
        ]
        
        df_votes = None
        for path in file_paths:
            try:
                abs_path = os.path.abspath(path) if not os.path.isabs(path) else path
                if os.path.exists(abs_path) and os.path.getsize(abs_path) > 0:
                    df_votes = pd.read_csv(abs_path)
                    if not df_votes.empty:
                        break
            except (FileNotFoundError, pd.errors.EmptyDataError, pd.errors.ParserError, Exception):
                continue
        
        if df_votes is None or df_votes.empty:
            return pd.DataFrame()
        
        # Convert numeric columns
        numeric_cols = ['votes', 'pct_votes', 'ranking']
        for col in numeric_cols:
            if col in df_votes.columns:
                df_votes[col] = pd.to_numeric(df_votes[col], errors='coerce').fillna(0)
        
        return df_votes
    except Exception as e:
        return pd.DataFrame()

@st.cache_data
def load_bribes_data():
    """Load bribes and gauges enriched data"""
    try:
        # Get current working directory (where streamlit is run from)
        cwd = os.getcwd()
        
        # Try different possible file names and paths (in order of likelihood)
        file_paths = [
            os.path.abspath(os.path.join(cwd, '..', 'data', 'Balancer_Bribes_Gauges_enriched.csv')),  # ../data/file.csv
            os.path.abspath(os.path.join(cwd, '..', 'data', 'balancer_bribes_gauges_enriched.csv')),
            os.path.abspath(os.path.join(cwd, '..', 'data', 'Balancer_Bribes_Gauges.csv')),
            os.path.abspath(os.path.join(cwd, 'data', 'Balancer_Bribes_Gauges_enriched.csv')),  # data/file.csv
            os.path.abspath(os.path.join(cwd, 'data', 'balancer_bribes_gauges_enriched.csv')),
            'data/Balancer_Bribes_Gauges_enriched.csv',  # relative
            'data/balancer_bribes_gauges_enriched.csv',
            'Balancer_Bribes_Gauges_enriched.csv'  # current dir
        ]
        
        df_bribes = None
        for path in file_paths:
            try:
                abs_path = os.path.abspath(path) if not os.path.isabs(path) else path
                if os.path.exists(abs_path) and os.path.getsize(abs_path) > 0:
                    df_bribes = pd.read_csv(abs_path)
                    if not df_bribes.empty:
                        break
            except (FileNotFoundError, pd.errors.EmptyDataError, pd.errors.ParserError, Exception):
                continue
        
        if df_bribes is None or df_bribes.empty:
            return pd.DataFrame()
        
        # Convert date columns if they exist
        date_cols = ['date', 'block_date', 'timestamp', 'week', 'period']
        for col in date_cols:
            if col in df_bribes.columns:
                df_bribes[col] = pd.to_datetime(df_bribes[col], errors='coerce')
        
        # Convert numeric columns
        numeric_cols = [
            'bribe_amount_usd', 'bribe_amount', 'total_bribes_usd',
            'votes_received', 'bal_received', 'bal_emitted',
            'bribe_efficiency', 'bribe_per_vote', 'votes_per_bribe',
            'gauge_weight', 'gauge_share', 'bribe_count'
        ]
        
        for col in numeric_cols:
            if col in df_bribes.columns:
                df_bribes[col] = pd.to_numeric(df_bribes[col], errors='coerce').fillna(0)
        
        return df_bribes
    except FileNotFoundError:
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading bribes data: {str(e)}")
        return pd.DataFrame()

def get_top_pools(df, n=20):
    pool_agg = df.groupby('pool_symbol')['dao_profit_usd'].sum().sort_values(ascending=False).head(n)
    return pool_agg.index.tolist()

def get_worst_pools(df, n=20):
    pool_agg = df.groupby('pool_symbol')['dao_profit_usd'].sum().sort_values(ascending=True).head(n)
    return pool_agg.index.tolist()

def run_simulation_sidebar(df):
    st.sidebar.markdown("### ⚖️ Simulation Controls")
    
    st.sidebar.markdown("**1. Protocol Fee Percentage**")
    protocol_fee_pct = st.sidebar.slider(
        "Protocol Fee (%)",
        min_value=0,
        max_value=100,
        value=50,
        step=5,
        help="Percentage of total fees that goes to the protocol before distribution"
    )
    st.sidebar.markdown("**2. Revenue Share**")
    st.sidebar.caption("Division of remaining revenue after protocol fee")
    
    with st.sidebar.expander("📊 Non-Core Pools", expanded=True):
        nc_dao_pct = st.slider(
            "DAO Share (%)",
            min_value=0,
            max_value=100,
            value=50,
            step=1,
            key='nc_dao'
        )
        nc_holders_pct = 100 - nc_dao_pct
        st.caption(f"veBAL/BAL Holders: {nc_holders_pct}%")
    
    with st.sidebar.expander("⭐ Core Pools", expanded=True):
        c_dao_pct = st.slider(
            "DAO Share (%)",
            min_value=0,
            max_value=100,
            value=18,
            step=1,
            key='c_dao'
        )
        remaining_core = 100 - c_dao_pct
        c_holders_pct = st.slider(
            "veBAL/BAL Holders (%)",
            min_value=0,
            max_value=remaining_core,
            value=min(22, remaining_core),
            step=1,
            key='c_holders'
        )
        c_incentives_pct = 100 - c_dao_pct - c_holders_pct
        st.caption(f"Incentives (Tribes): {c_incentives_pct}%")
    
    st.sidebar.markdown("**3. Emissions**")
    emissions_per_week = st.sidebar.slider(
        "BAL Emitted per Week",
        min_value=0,
        max_value=200_000,
        value=86_000,
        step=1_000,
        help="Amount of BAL emitted per week, distributed proportionally to votes"
    )
    
    df_sim = df.copy()
    
    mask_core = df_sim['is_core_pool'] == 1
    mask_noncore = df_sim['is_core_pool'] == 0
    
    df_sim['sim_protocol_fee'] = df_sim['total_protocol_fee_usd'] * (protocol_fee_pct / 100)
    df_sim['remaining_revenue'] = df_sim['total_protocol_fee_usd'] - df_sim['sim_protocol_fee']
    
    df_sim['sim_dao_revenue'] = 0.0
    df_sim['sim_holders_revenue'] = 0.0
    df_sim['sim_incentives_revenue'] = 0.0
    
    df_sim.loc[mask_noncore, 'sim_dao_revenue'] = (
        df_sim.loc[mask_noncore, 'remaining_revenue'] * (nc_dao_pct / 100)
    )
    df_sim.loc[mask_noncore, 'sim_holders_revenue'] = (
        df_sim.loc[mask_noncore, 'remaining_revenue'] * (nc_holders_pct / 100)
    )
    
    df_sim.loc[mask_core, 'sim_dao_revenue'] = (
        df_sim.loc[mask_core, 'remaining_revenue'] * (c_dao_pct / 100)
    )
    df_sim.loc[mask_core, 'sim_holders_revenue'] = (
        df_sim.loc[mask_core, 'remaining_revenue'] * (c_holders_pct / 100)
    )
    df_sim.loc[mask_core, 'sim_incentives_revenue'] = (
        df_sim.loc[mask_core, 'remaining_revenue'] * (c_incentives_pct / 100)
    )
    
    df_sim['week'] = df_sim['block_date'].dt.to_period('W').dt.start_time
    weekly_votes = df_sim.groupby('week')['votes_received'].sum()
    
    df_sim['weekly_total_votes'] = df_sim['week'].map(weekly_votes)
    df_sim['vote_share'] = np.where(
        df_sim['weekly_total_votes'] > 0,
        df_sim['votes_received'] / df_sim['weekly_total_votes'],
        0
    )
    
    df_sim['sim_bal_emitted'] = df_sim['vote_share'] * emissions_per_week
    
    df_sim.attrs['protocol_fee_pct'] = protocol_fee_pct
    df_sim.attrs['emissions_per_week'] = emissions_per_week
    df_sim.attrs['nc_dao_pct'] = nc_dao_pct
    df_sim.attrs['nc_holders_pct'] = nc_holders_pct
    df_sim.attrs['c_dao_pct'] = c_dao_pct
    df_sim.attrs['c_holders_pct'] = c_holders_pct
    df_sim.attrs['c_incentives_pct'] = c_incentives_pct
    
    return df_sim

def create_minimalist_chart(x, y, name, color, height=400):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x,
        y=y,
        mode='lines',
        name=name,
        line=dict(color=color, width=1.5),
        hovertemplate='%{y:,.0f}<extra></extra>'
    ))
    
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=height,
        margin=dict(l=40, r=20, t=20, b=40),
        xaxis=dict(
            showgrid=False,
            showline=True,
            linecolor='rgba(255,255,255,0.1)',
            title="",
            tickfont=dict(size=11, color='#8B95A6')
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(255,255,255,0.05)',
            showline=False,
            title="",
            tickfont=dict(size=11, color='#8B95A6')
        ),
        hovermode='x unified',
        showlegend=False
    )
    
    return fig

def calculate_emission_reduction_impact(df, reduction_factor):
    df_scenario = df.copy()
    
    if 'sim_bal_emitted' in df_scenario.columns:
        df_scenario['reduced_bal_emitted'] = df_scenario['sim_bal_emitted'] * reduction_factor
    else:
        df_scenario['reduced_bal_emitted'] = df_scenario['bal_emited_votes'] * reduction_factor
    
    if 'direct_incentives' in df_scenario.columns:
        df_scenario['reduced_incentives'] = df_scenario['direct_incentives'] * reduction_factor
    else:
        df_scenario['reduced_incentives'] = 0
    
    if 'sim_dao_revenue' in df_scenario.columns:
        df_scenario['new_dao_profit'] = df_scenario['sim_dao_revenue'] - df_scenario['reduced_incentives']
    else:
        df_scenario['new_dao_profit'] = df_scenario['protocol_fee_amount_usd'] - df_scenario['reduced_incentives']
    
    return df_scenario
