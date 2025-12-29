# ============================================================
# ivolatility_backtesting.py - ENHANCED VERSION
# 
# NEW FEATURES:
# 1. Combined stop-loss (requires BOTH conditions)
# 2. Parameter optimization framework
# 3. Optimization results visualization
# ============================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import ivolatility as ivol
import os
import time
import psutil
import warnings
from itertools import product
import sys
import gc
from typing import Dict, List, Optional, Tuple, Union, Any
warnings.filterwarnings('ignore', category=pd.errors.SettingWithCopyWarning)
warnings.filterwarnings('ignore', message='.*SettingWithCopyWarning.*')
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=DeprecationWarning)

sns.set_style('darkgrid')
plt.rcParams['figure.figsize'] = (15, 8)

# ============================================================
# STRATEGY REGISTRY v2.21 - SINGLE SOURCE OF TRUTH
# All strategy metadata in one place (data-driven)
# ============================================================
# 
# SAFETY BUFFER NOTE (1.5x multiplier in risk_formula):
# ======================================================
# All risk_formula entries use 1.5x multiplier for EOD backtests.
# This 50% buffer accounts for:
#   • Slippage: Bid/ask spread worse than historical data (+10-20%)
#   • Gap risk: Overnight price jumps, no intraday control (+10-30%)
#   • Volatility spikes: IV explosions during market stress (+10-20%)
#   • Conservative estimation: Better to overestimate than underestimate
#
# REAL-WORLD COMPARISON:
#   • Broker margin requirements: 1.0x (just theoretical max loss)
#   • TastyTrade/OptionAlpha: 1.0x (buying power reduction)
#   • This framework: 1.5x (conservative for EOD backtests)
#   • Academic papers: varies 1.0x-2.0x
#
# ALTERNATIVES by data type:
#   • EOD data: 1.5x (current, appropriate)
#   • Intraday data: 1.2x-1.3x (less buffer needed)
#   • Live simulation: 1.0x-1.1x (closest to reality)
#
# This buffer is applied CONSISTENTLY in both:
#   1. Market-based calculation (calculate_available_capital with current prices)
#   2. Theoretical calculation (StrategyRegistry.calculate_risk with risk_formula)
#
# Example: IRON_CONDOR risk_formula below
#   → 'max((wing_width * 100 - credit/contracts) * contracts * 1.5, credit * 2)'
#                                                                  ^^^^ 1.5x buffer
# ============================================================

STRATEGIES = {
    'IRON_CONDOR': {
        'name': 'Iron Condor',
        'category': 'CREDIT',
        'risk_formula': 'max((wing_width * 100 - credit/contracts) * contracts * 1.5, credit * 2)',
        'required_fields': ['wing_width', 'contracts', 'total_cost'],
        
        # Strategy defaults (auto-applied if missing from config)
        'defaults': {
            'profit_target': 0.50,  # 50% of max profit (standard for credit strategies)
        },
        
        # Config parameters (for summary.txt export)
        'config_params': [
            {'key': 'wing_width', 'label': 'Wing Width', 'format': '${:.0f}', 'in_summary': True},
            {'key': 'call_delta_target', 'label': 'Call Delta Target', 'format': '{:.2f}', 'in_summary': True},
            {'key': 'put_delta_target', 'label': 'Put Delta Target', 'format': '{:.2f}', 'in_summary': True},
            {'key': 'dte_target', 'label': 'DTE Target', 'format': '{:.0f} days', 'in_summary': True},
            {'key': 'profit_target', 'label': 'Profit Target', 'format': '{:.0%}', 'in_summary': True},
            {'key': 'position_size_pct', 'label': 'Position Size', 'format': '{:.1%} of capital', 'in_summary': True},
        ],
        
        # Position data (for trades CSV columns)
        'parameters': {
            'wing_width': {'label': 'Wing Width', 'format': '${:.0f}', 'csv': True, 'debug': True},
            'call_delta': {'label': 'Call Delta', 'format': '{:.3f}', 'csv': True, 'debug': True},
            'put_delta': {'label': 'Put Delta', 'format': '{:.3f}', 'csv': True, 'debug': True},
            'total_credit': {'label': 'Total Credit', 'format': '${:.2f}', 'csv': True, 'debug': True},
            'call_spread_credit': {'label': '  • Call Spread', 'format': '${:.2f}', 'csv': True, 'debug': True},
            'put_spread_credit': {'label': '  • Put Spread', 'format': '${:.2f}', 'csv': True, 'debug': True},
            'max_risk': {'label': 'Max Risk/Contract', 'format': '${:.2f}', 'csv': True, 'debug': True},
            'iv_rank': {'label': 'IV Rank', 'format': '{:.1f}%', 'csv': True, 'debug': True},
        },
        
        # File naming (for optimization exports)
        'file_naming': {
            'signature': ['wing_width', 'call_delta_target'],
            'format': [
                {'key': 'wing_width', 'code': 'WW', 'formatter': lambda x: f"{int(x)}"},
                {'key': 'call_delta_target', 'code': 'CD', 'formatter': lambda x: f"{int(x*100)}"},
                {'key': 'put_delta_target', 'code': 'PD', 'formatter': lambda x: f"{int(x*100)}"},
                {'key': 'dte_target', 'code': 'DT', 'formatter': lambda x: f"{int(x)}"},
                {'key': 'profit_target', 'code': 'PT', 'formatter': lambda x: f"{int(x*100)}"},
                {'key': 'position_size_pct', 'code': 'PS', 'formatter': lambda x: f"{x:.2f}".rstrip('0').rstrip('.')},
            ]
        },
        
        # Leg structure (for CSV export fields)
        'legs': [
            {'name': 'short_call', 'fields': ['bid', 'ask'], 'greeks': ['delta', 'gamma', 'vega', 'theta'], 'iv': True},
            {'name': 'long_call', 'fields': ['bid', 'ask'], 'greeks': ['delta', 'gamma', 'vega', 'theta'], 'iv': True},
            {'name': 'short_put', 'fields': ['bid', 'ask'], 'greeks': ['delta', 'gamma', 'vega', 'theta'], 'iv': True},
            {'name': 'long_put', 'fields': ['bid', 'ask'], 'greeks': ['delta', 'gamma', 'vega', 'theta'], 'iv': True},
        ],
        
        # Indicators (optional - for entry filtering)
        'indicators': [
            {
                'name': 'iv_rank_ivx',  # ✅ NEW: Uses IVX data (no lookback needed!)
                'required': False,
                'params_from_config': []  # No params needed - IVX has built-in high/low!
            },
            {
                'name': 'iv_skew',
                'required': False,
                'params_from_config': ['dte_target', 'delta_otm']  # ✅ BOTH params needed!
            }
        ],
        
        # ✅ Options filter for stock-opts-by-param (20x less data!)
        'options_filter': {
            'selection_type': 'delta',     # Delta-based strategy
            'delta_from': 0.0,            # Wide range to match options-rawiv
            'delta_to': 1.0,              # Wide range to match options-rawiv
            'dte_tracking_min': 0,         # ✅ CRITICAL: Track until expiration (0 DTE) to avoid intrinsic settlement disasters!
        },
    },
    'BULL_PUT_SPREAD': {
        'name': 'Bull Put Spread',
        'category': 'CREDIT',
        'risk_formula': 'max((spread_width * 100 * contracts - credit) * 1.5, credit * 2)',
        'required_fields': ['short_strike', 'long_strike', 'contracts', 'total_cost'],
        
        # Strategy defaults (auto-applied if missing from config)
        'defaults': {
            'profit_target': 0.50,  # 50% of max profit (standard for credit strategies)
        },
        
        'config_params': [
            {'key': 'spread_width', 'label': 'Spread Width', 'format': '${:.0f}', 'in_summary': True},
            {'key': 'delta_target', 'label': 'Delta Target', 'format': '{:.2f}', 'in_summary': True},
            {'key': 'dte_target', 'label': 'DTE Target', 'format': '{:.0f} days', 'in_summary': True},
            {'key': 'profit_target', 'label': 'Profit Target', 'format': '{:.0%}', 'in_summary': True},
            {'key': 'position_size_pct', 'label': 'Position Size', 'format': '{:.1%} of capital', 'in_summary': True},
        ],
        'parameters': {
            'spread_width': {'label': 'Spread Width', 'format': '${:.0f}', 'csv': True, 'debug': True},
            'credit': {'label': 'Credit', 'format': '${:.2f}', 'csv': True, 'debug': True},
            'max_risk': {'label': 'Max Risk', 'format': '${:.2f}', 'csv': True, 'debug': True},
            'short_delta': {'label': 'Short Delta', 'format': '{:.3f}', 'csv': True, 'debug': True},
        },
        'file_naming': {
            'signature': ['spread_width', 'delta_target'],
            'format': [
                {'key': 'spread_width', 'code': 'SW', 'formatter': lambda x: f"{int(x)}"},
                {'key': 'delta_target', 'code': 'D', 'formatter': lambda x: f"{int(x*100)}"},
                {'key': 'dte_target', 'code': 'DT', 'formatter': lambda x: f"{int(x)}"},
                {'key': 'profit_target', 'code': 'PT', 'formatter': lambda x: f"{int(x*100)}"},
                {'key': 'position_size_pct', 'code': 'PS', 'formatter': lambda x: f"{x:.2f}".rstrip('0').rstrip('.')},
            ]
        },
        
        # Leg structure (for CSV export fields)
        'legs': [
            {'name': 'short', 'fields': ['bid', 'ask'], 'greeks': ['delta', 'gamma', 'vega', 'theta'], 'iv': True},
            {'name': 'long', 'fields': ['bid', 'ask'], 'greeks': ['delta', 'gamma', 'vega', 'theta'], 'iv': True},
        ],
        
        'indicators': [],
        
        # ✅ Options filter for stock-opts-by-param
        'options_filter': {
            'selection_type': 'delta',
            'delta_from': 0.0,            # Wide range to match options-rawiv
            'delta_to': 1.0,              # Wide range to match options-rawiv
            'dte_tracking_min': 0,         # ✅ Track until expiration (0 DTE)
        },
    },
    'BEAR_CALL_SPREAD': {
        'name': 'Bear Call Spread',
        'category': 'CREDIT',
        'risk_formula': 'max((spread_width * 100 * contracts - credit) * 1.5, credit * 2)',
        'required_fields': ['short_strike', 'long_strike', 'contracts', 'total_cost'],
        
        # Strategy defaults (auto-applied if missing from config)
        'defaults': {
            'profit_target': 0.50,  # 50% of max profit (standard for credit strategies)
        },
        
        'config_params': [
            {'key': 'spread_width', 'label': 'Spread Width', 'format': '${:.0f}', 'in_summary': True},
            {'key': 'delta_target', 'label': 'Delta Target', 'format': '{:.2f}', 'in_summary': True},
            {'key': 'dte_target', 'label': 'DTE Target', 'format': '{:.0f} days', 'in_summary': True},
            {'key': 'profit_target', 'label': 'Profit Target', 'format': '{:.0%}', 'in_summary': True},
            {'key': 'position_size_pct', 'label': 'Position Size', 'format': '{:.1%} of capital', 'in_summary': True},
        ],
        'parameters': {
            'spread_width': {'label': 'Spread Width', 'format': '${:.0f}', 'csv': True, 'debug': True},
            'credit': {'label': 'Credit', 'format': '${:.2f}', 'csv': True, 'debug': True},
            'max_risk': {'label': 'Max Risk', 'format': '${:.2f}', 'csv': True, 'debug': True},
            'short_delta': {'label': 'Short Delta', 'format': '{:.3f}', 'csv': True, 'debug': True},
        },
        'file_naming': {
            'signature': ['spread_width', 'delta_target'],
            'format': [
                {'key': 'spread_width', 'code': 'SW', 'formatter': lambda x: f"{int(x)}"},
                {'key': 'delta_target', 'code': 'D', 'formatter': lambda x: f"{int(x*100)}"},
                {'key': 'dte_target', 'code': 'DT', 'formatter': lambda x: f"{int(x)}"},
                {'key': 'profit_target', 'code': 'PT', 'formatter': lambda x: f"{int(x*100)}"},
                {'key': 'position_size_pct', 'code': 'PS', 'formatter': lambda x: f"{x:.2f}".rstrip('0').rstrip('.')},
            ]
        },
        
        # Leg structure (for CSV export fields)
        'legs': [
            {'name': 'short', 'fields': ['bid', 'ask'], 'greeks': ['delta', 'gamma', 'vega', 'theta'], 'iv': True},
            {'name': 'long', 'fields': ['bid', 'ask'], 'greeks': ['delta', 'gamma', 'vega', 'theta'], 'iv': True},
        ],
        
        'indicators': [],
        
        # ✅ Options filter for stock-opts-by-param
        'options_filter': {
            'selection_type': 'delta',
            'delta_from': 0.0,            # Wide range to match options-rawiv
            'delta_to': 1.0,              # Wide range to match options-rawiv
            'dte_tracking_min': 0,         # ✅ Track until expiration (0 DTE)
        },
    },
    'CREDIT_SPREAD': {
        'name': 'Credit Spread',
        'category': 'CREDIT',
        'risk_formula': 'max((spread_width * 100 * contracts - credit) * 1.5, credit * 2)',
        'required_fields': ['short_strike', 'long_strike', 'contracts', 'total_cost'],
        
        # Strategy defaults (auto-applied if missing from config)
        'defaults': {
            'profit_target': 0.50,  # 50% of max profit (standard for credit strategies)
        },
        
        'config_params': [
            {'key': 'spread_width', 'label': 'Spread Width', 'format': '${:.0f}', 'in_summary': True},
            {'key': 'delta_target', 'label': 'Delta Target', 'format': '{:.2f}', 'in_summary': True},
            {'key': 'dte_target', 'label': 'DTE Target', 'format': '{:.0f} days', 'in_summary': True},
            {'key': 'profit_target', 'label': 'Profit Target', 'format': '{:.0%}', 'in_summary': True},
            {'key': 'position_size_pct', 'label': 'Position Size', 'format': '{:.1%} of capital', 'in_summary': True},
        ],
        'parameters': {
            'spread_width': {'label': 'Spread Width', 'format': '${:.0f}', 'csv': True, 'debug': True},
            'credit': {'label': 'Credit', 'format': '${:.2f}', 'csv': True, 'debug': True},
            'max_risk': {'label': 'Max Risk', 'format': '${:.2f}', 'csv': True, 'debug': True},
        },
        'file_naming': {
            'signature': ['spread_width', 'delta_target'],
            'format': [
                {'key': 'spread_width', 'code': 'SW', 'formatter': lambda x: f"{int(x)}"},
                {'key': 'delta_target', 'code': 'D', 'formatter': lambda x: f"{int(x*100)}"},
                {'key': 'dte_target', 'code': 'DT', 'formatter': lambda x: f"{int(x)}"},
                {'key': 'profit_target', 'code': 'PT', 'formatter': lambda x: f"{int(x*100)}"},
                {'key': 'position_size_pct', 'code': 'PS', 'formatter': lambda x: f"{x:.2f}".rstrip('0').rstrip('.')},
            ]
        },
        
        # Leg structure (for CSV export fields)
        'legs': [
            {'name': 'short', 'fields': ['bid', 'ask'], 'greeks': ['delta', 'gamma', 'vega', 'theta'], 'iv': True},
            {'name': 'long', 'fields': ['bid', 'ask'], 'greeks': ['delta', 'gamma', 'vega', 'theta'], 'iv': True},
        ],
        
        'indicators': [],
        
        # ✅ Options filter for stock-opts-by-param
        'options_filter': {
            'selection_type': 'delta',
            'delta_from': 0.0,            # Wide range to match options-rawiv
            'delta_to': 1.0,              # Wide range to match options-rawiv
            'dte_tracking_min': 0,         # ✅ Track until expiration (0 DTE)
        },
    },
    'BULL_CALL_SPREAD': {
        'name': 'Bull Call Spread',
        'category': 'DEBIT',
        'risk_formula': 'debit * 1.5',
        'required_fields': ['total_cost'],
        'legs': [
            {'name': 'long_call', 'fields': ['bid', 'ask'], 'greeks': ['delta', 'gamma', 'vega', 'theta'], 'iv': True},
            {'name': 'short_call', 'fields': ['bid', 'ask'], 'greeks': ['delta', 'gamma', 'vega', 'theta'], 'iv': True},
        ],
        'config_params': [
            {'key': 'spread_width', 'label': 'Spread Width', 'format': '${:.0f}', 'in_summary': True},
            {'key': 'delta_target', 'label': 'Delta Target', 'format': '{:.2f}', 'in_summary': True},
            {'key': 'dte_target', 'label': 'DTE Target', 'format': '{:.0f} days', 'in_summary': True},
            {'key': 'position_size_pct', 'label': 'Position Size', 'format': '{:.1%} of capital', 'in_summary': True},
        ],
        'parameters': {
            'spread_width': {'label': 'Spread Width', 'format': '${:.0f}', 'csv': True, 'debug': True},
            'debit': {'label': 'Debit Paid', 'format': '${:.2f}', 'csv': True, 'debug': True},
            'max_profit': {'label': 'Max Profit', 'format': '${:.2f}', 'csv': True, 'debug': True},
        },
        'file_naming': {
            'signature': ['spread_width', 'delta_target'],
            'format': [
                {'key': 'spread_width', 'code': 'SW', 'formatter': lambda x: f"{int(x)}"},
                {'key': 'delta_target', 'code': 'D', 'formatter': lambda x: f"{int(x*100)}"},
                {'key': 'dte_target', 'code': 'DT', 'formatter': lambda x: f"{int(x)}"},
                {'key': 'position_size_pct', 'code': 'PS', 'formatter': lambda x: f"{x:.2f}".rstrip('0').rstrip('.')},
            ]
        },
        
        # Leg structure (for CSV export fields)
        'legs': [
            {'name': 'short', 'fields': ['bid', 'ask'], 'greeks': ['delta', 'gamma', 'vega', 'theta'], 'iv': True},
            {'name': 'long', 'fields': ['bid', 'ask'], 'greeks': ['delta', 'gamma', 'vega', 'theta'], 'iv': True},
        ],
        
        # ✅ Options filter for stock-opts-by-param
        'options_filter': {
            'selection_type': 'delta',
            'delta_from': 0.0,            # Wide range to match options-rawiv
            'delta_to': 1.0,              # Wide range to match options-rawiv
            'dte_tracking_min': 0,         # ✅ Track until expiration (0 DTE)
        },
    },
    'BEAR_PUT_SPREAD': {
        'name': 'Bear Put Spread',
        'category': 'DEBIT',
        'risk_formula': 'debit * 1.5',
        'required_fields': ['total_cost'],
        'legs': [
            {'name': 'long_put', 'fields': ['bid', 'ask'], 'greeks': ['delta', 'gamma', 'vega', 'theta'], 'iv': True},
            {'name': 'short_put', 'fields': ['bid', 'ask'], 'greeks': ['delta', 'gamma', 'vega', 'theta'], 'iv': True},
        ],
        'config_params': [
            {'key': 'spread_width', 'label': 'Spread Width', 'format': '${:.0f}', 'in_summary': True},
            {'key': 'delta_target', 'label': 'Delta Target', 'format': '{:.2f}', 'in_summary': True},
            {'key': 'dte_target', 'label': 'DTE Target', 'format': '{:.0f} days', 'in_summary': True},
            {'key': 'position_size_pct', 'label': 'Position Size', 'format': '{:.1%} of capital', 'in_summary': True},
        ],
        'parameters': {
            'spread_width': {'label': 'Spread Width', 'format': '${:.0f}', 'csv': True, 'debug': True},
            'debit': {'label': 'Debit Paid', 'format': '${:.2f}', 'csv': True, 'debug': True},
            'max_profit': {'label': 'Max Profit', 'format': '${:.2f}', 'csv': True, 'debug': True},
        },
        'file_naming': {
            'signature': ['spread_width', 'delta_target'],
            'format': [
                {'key': 'spread_width', 'code': 'SW', 'formatter': lambda x: f"{int(x)}"},
                {'key': 'delta_target', 'code': 'D', 'formatter': lambda x: f"{int(x*100)}"},
                {'key': 'dte_target', 'code': 'DT', 'formatter': lambda x: f"{int(x)}"},
                {'key': 'position_size_pct', 'code': 'PS', 'formatter': lambda x: f"{x:.2f}".rstrip('0').rstrip('.')},
            ]
        },
        
        # Leg structure (for CSV export fields)
        'legs': [
            {'name': 'short', 'fields': ['bid', 'ask'], 'greeks': ['delta', 'gamma', 'vega', 'theta'], 'iv': True},
            {'name': 'long', 'fields': ['bid', 'ask'], 'greeks': ['delta', 'gamma', 'vega', 'theta'], 'iv': True},
        ],
        
        # ✅ Options filter for stock-opts-by-param
        'options_filter': {
            'selection_type': 'delta',
            'delta_from': 0.0,            # Wide range to match options-rawiv
            'delta_to': 1.0,              # Wide range to match options-rawiv
            'dte_tracking_min': 0,         # ✅ Track until expiration (0 DTE)
        },
        
        'indicators': [],
    },
    'DEBIT_SPREAD': {
        'name': 'Debit Spread',
        'category': 'DEBIT',
        'risk_formula': 'debit * 1.5',
        'required_fields': ['total_cost'],
        'config_params': [
            {'key': 'spread_width', 'label': 'Spread Width', 'format': '${:.0f}', 'in_summary': True},
            {'key': 'delta_target', 'label': 'Delta Target', 'format': '{:.2f}', 'in_summary': True},
            {'key': 'dte_target', 'label': 'DTE Target', 'format': '{:.0f} days', 'in_summary': True},
            {'key': 'position_size_pct', 'label': 'Position Size', 'format': '{:.1%} of capital', 'in_summary': True},
        ],
        'parameters': {
            'spread_width': {'label': 'Spread Width', 'format': '${:.0f}', 'csv': True, 'debug': True},
            'debit': {'label': 'Debit Paid', 'format': '${:.2f}', 'csv': True, 'debug': True},
            'max_profit': {'label': 'Max Profit', 'format': '${:.2f}', 'csv': True, 'debug': True},
        },
        'file_naming': {
            'signature': ['spread_width', 'delta_target'],
            'format': [
                {'key': 'spread_width', 'code': 'SW', 'formatter': lambda x: f"{int(x)}"},
                {'key': 'delta_target', 'code': 'D', 'formatter': lambda x: f"{int(x*100)}"},
                {'key': 'dte_target', 'code': 'DT', 'formatter': lambda x: f"{int(x)}"},
                {'key': 'position_size_pct', 'code': 'PS', 'formatter': lambda x: f"{x:.2f}".rstrip('0').rstrip('.')},
            ]
        },
        
        # Leg structure (for CSV export fields)
        'legs': [
            {'name': 'short', 'fields': ['bid', 'ask'], 'greeks': ['delta', 'gamma', 'vega', 'theta'], 'iv': True},
            {'name': 'long', 'fields': ['bid', 'ask'], 'greeks': ['delta', 'gamma', 'vega', 'theta'], 'iv': True},
        ],
        
        # ✅ Options filter for stock-opts-by-param
        'options_filter': {
            'selection_type': 'delta',
            'delta_from': 0.0,            # Wide range to match options-rawiv
            'delta_to': 1.0,              # Wide range to match options-rawiv
            'dte_tracking_min': 0,         # ✅ Track until expiration (0 DTE)
        },
    },
    'IRON_BUTTERFLY': {
        'name': 'Iron Butterfly',
        'category': 'CREDIT',
        'risk_formula': 'max((wing_width * 100 * contracts - credit) * 1.5, credit * 2)',
        'required_fields': ['wing_width', 'contracts', 'total_cost'],
        
        # Strategy defaults (auto-applied if missing from config)
        'defaults': {
            'profit_target': 0.50,  # 50% of max profit (standard for credit strategies)
        },
        
        'config_params': [
            {'key': 'wing_width', 'label': 'Wing Width', 'format': '${:.0f}', 'in_summary': True},
            {'key': 'atm_strike', 'label': 'ATM Strike', 'format': '${:.0f}', 'in_summary': True},
            {'key': 'dte_target', 'label': 'DTE Target', 'format': '{:.0f} days', 'in_summary': True},
            {'key': 'position_size_pct', 'label': 'Position Size', 'format': '{:.1%} of capital', 'in_summary': True},
        ],
        'parameters': {
            'wing_width': {'label': 'Wing Width', 'format': '${:.0f}', 'csv': True, 'debug': True},
            'atm_strike': {'label': 'ATM Strike', 'format': '${:.0f}', 'csv': True, 'debug': True},
            'total_credit': {'label': 'Total Credit', 'format': '${:.2f}', 'csv': True, 'debug': True},
            'max_risk': {'label': 'Max Risk', 'format': '${:.2f}', 'csv': True, 'debug': True},
        },
        'file_naming': {
            'signature': ['wing_width', 'atm_strike'],
            'format': [
                {'key': 'wing_width', 'code': 'WW', 'formatter': lambda x: f"{int(x)}"},
                {'key': 'atm_strike', 'code': 'ATM', 'formatter': lambda x: f"{int(x)}"},
                {'key': 'dte_target', 'code': 'DT', 'formatter': lambda x: f"{int(x)}"},
                {'key': 'position_size_pct', 'code': 'PS', 'formatter': lambda x: f"{x:.2f}".rstrip('0').rstrip('.')},
            ]
        },
        
        # Leg structure (for CSV export fields)
        'legs': [
            {'name': 'short_call', 'fields': ['bid', 'ask'], 'greeks': ['delta', 'gamma', 'vega', 'theta'], 'iv': True},
            {'name': 'long_call', 'fields': ['bid', 'ask'], 'greeks': ['delta', 'gamma', 'vega', 'theta'], 'iv': True},
            {'name': 'short_put', 'fields': ['bid', 'ask'], 'greeks': ['delta', 'gamma', 'vega', 'theta'], 'iv': True},
            {'name': 'long_put', 'fields': ['bid', 'ask'], 'greeks': ['delta', 'gamma', 'vega', 'theta'], 'iv': True},
        ],
        
        'indicators': [],
        
        # ✅ Options filter for stock-opts-by-param (full delta range)
        'options_filter': {
            'selection_type': 'delta',
            'delta_from': 0.0,             # Full range to capture ITM/OTM after big moves
            'delta_to': 1.0,
            'dte_tracking_min': 0,         # ✅ Track until expiration (0 DTE)
        },
    },
    'BUTTERFLY': {
        'name': 'Butterfly',
        'category': 'DEBIT',
        'risk_formula': 'net_debit * 1.5',
        'required_fields': ['total_cost'],
        'config_params': [
            {'key': 'wing_width', 'label': 'Wing Width', 'format': '${:.0f}', 'in_summary': True},
            {'key': 'center_strike', 'label': 'Center Strike', 'format': '{}', 'in_summary': True},
            {'key': 'dte_target', 'label': 'DTE Target', 'format': '{:.0f} days', 'in_summary': True},
            {'key': 'position_size_pct', 'label': 'Position Size', 'format': '{:.1%} of capital', 'in_summary': True},
        ],
        'parameters': {
            'wing_width': {'label': 'Wing Width', 'format': '${:.0f}', 'csv': True, 'debug': True},
            'center_strike': {'label': 'Center Strike', 'format': '${:.0f}', 'csv': True, 'debug': True},
            'net_debit': {'label': 'Net Debit', 'format': '${:.2f}', 'csv': True, 'debug': True},
            'max_profit': {'label': 'Max Profit', 'format': '${:.2f}', 'csv': True, 'debug': True},
        },
        'file_naming': {
            'signature': ['wing_width', 'center_strike'],
            'format': [
                {'key': 'wing_width', 'code': 'WW', 'formatter': lambda x: f"{int(x)}"},
                {'key': 'center_strike', 'code': '', 'formatter': lambda x: str(x)},
                {'key': 'dte_target', 'code': 'DT', 'formatter': lambda x: f"{int(x)}"},
                {'key': 'position_size_pct', 'code': 'PS', 'formatter': lambda x: f"{x:.2f}".rstrip('0').rstrip('.')},
            ]
        },
        
        # Leg structure (for CSV export fields)
        'legs': [
            {'name': 'lower_wing', 'fields': ['bid', 'ask'], 'greeks': ['delta', 'gamma', 'vega', 'theta'], 'iv': True},
            {'name': 'body1', 'fields': ['bid', 'ask'], 'greeks': ['delta', 'gamma', 'vega', 'theta'], 'iv': True},
            {'name': 'body2', 'fields': ['bid', 'ask'], 'greeks': ['delta', 'gamma', 'vega', 'theta'], 'iv': True},
            {'name': 'upper_wing', 'fields': ['bid', 'ask'], 'greeks': ['delta', 'gamma', 'vega', 'theta'], 'iv': True},
        ],
        
        # ✅ Options filter for stock-opts-by-param (full delta range)
        'options_filter': {
            'selection_type': 'delta',
            'delta_from': 0.0,             # Full range to capture ITM/OTM after big moves
            'delta_to': 1.0,
            'dte_tracking_min': 0,         # ✅ Track until expiration (0 DTE)
        },
    },
    'CALENDAR_SPREAD': {
        'name': 'Calendar Spread',
        'category': 'DEBIT',
        'risk_formula': 'net_debit * 2',
        'required_fields': ['total_cost'],
        'config_params': [
            {'key': 'front_dte', 'label': 'Front DTE', 'format': '{:.0f} days', 'in_summary': True},
            {'key': 'back_dte', 'label': 'Back DTE', 'format': '{:.0f} days', 'in_summary': True},
            {'key': 'strike_selection', 'label': 'Strike Selection', 'format': '{}', 'in_summary': True},
            {'key': 'delta_target', 'label': 'Delta Target', 'format': '{:.2f}', 'in_summary': True},
            {'key': 'position_size_pct', 'label': 'Position Size', 'format': '{:.1%} of capital', 'in_summary': True},
        ],
        'parameters': {
            'front_dte': {'label': 'Front DTE', 'format': '{:.0f} days', 'csv': True, 'debug': True},
            'back_dte': {'label': 'Back DTE', 'format': '{:.0f} days', 'csv': True, 'debug': True},
            'strike': {'label': 'Strike', 'format': '${:.0f}', 'csv': True, 'debug': True},
            'net_debit': {'label': 'Net Debit', 'format': '${:.2f}', 'csv': True, 'debug': True},
        },
        'file_naming': {
            'signature': ['front_dte', 'back_dte'],
            'format': [
                {'key': 'front_dte', 'code': 'FDT', 'formatter': lambda x: f"{int(x)}"},
                {'key': 'back_dte', 'code': 'BDT', 'formatter': lambda x: f"{int(x)}"},
                {'key': 'strike_selection', 'code': '', 'formatter': lambda x: str(x)},
                {'key': 'delta_target', 'code': 'D', 'formatter': lambda x: f"{int(x*100)}"},
                {'key': 'position_size_pct', 'code': 'PS', 'formatter': lambda x: f"{x:.2f}".rstrip('0').rstrip('.')},
            ]
        },
        
        # Leg structure (for CSV export fields)
        'legs': [
            {'name': 'front', 'fields': ['bid', 'ask'], 'greeks': ['delta', 'gamma', 'vega', 'theta'], 'iv': True},
            {'name': 'back', 'fields': ['bid', 'ask'], 'greeks': ['delta', 'gamma', 'vega', 'theta'], 'iv': True},
        ],
        
        'indicators': [],
        
        # ✅ Options filter for stock-opts-by-param
        'options_filter': {
            'selection_type': 'delta',
            'delta_from': 0.0,            # Wide range to match options-rawiv
            'delta_to': 1.0,              # Wide range to match options-rawiv
            'dte_tracking_min': 0,         # ✅ Track until expiration (0 DTE)
        },
    },
    'DIAGONAL_SPREAD': {
        'name': 'Diagonal Spread',
        'category': 'DEBIT',
        'risk_formula': 'net_debit * 2',
        'required_fields': ['total_cost'],
        'config_params': [
            {'key': 'front_dte', 'label': 'Front DTE', 'format': '{:.0f} days', 'in_summary': True},
            {'key': 'back_dte', 'label': 'Back DTE', 'format': '{:.0f} days', 'in_summary': True},
            {'key': 'strike_offset', 'label': 'Strike Offset', 'format': '${:.0f}', 'in_summary': True},
            {'key': 'delta_target', 'label': 'Delta Target', 'format': '{:.2f}', 'in_summary': True},
            {'key': 'position_size_pct', 'label': 'Position Size', 'format': '{:.1%} of capital', 'in_summary': True},
        ],
        'parameters': {
            'front_dte': {'label': 'Front DTE', 'format': '{:.0f} days', 'csv': True, 'debug': True},
            'back_dte': {'label': 'Back DTE', 'format': '{:.0f} days', 'csv': True, 'debug': True},
            'strike_offset': {'label': 'Strike Offset', 'format': '${:.0f}', 'csv': True, 'debug': True},
            'net_debit': {'label': 'Net Debit', 'format': '${:.2f}', 'csv': True, 'debug': True},
        },
        'file_naming': {
            'signature': ['front_dte', 'back_dte', 'strike_offset'],
            'format': [
                {'key': 'front_dte', 'code': 'FDT', 'formatter': lambda x: f"{int(x)}"},
                {'key': 'back_dte', 'code': 'BDT', 'formatter': lambda x: f"{int(x)}"},
                {'key': 'strike_offset', 'code': 'SO', 'formatter': lambda x: f"{int(x)}"},
                {'key': 'delta_target', 'code': 'D', 'formatter': lambda x: f"{int(x*100)}"},
                {'key': 'position_size_pct', 'code': 'PS', 'formatter': lambda x: f"{x:.2f}".rstrip('0').rstrip('.')},
            ]
        },
        
        # Leg structure (for CSV export fields)
        'legs': [
            {'name': 'front', 'fields': ['bid', 'ask'], 'greeks': ['delta', 'gamma', 'vega', 'theta'], 'iv': True},
            {'name': 'back', 'fields': ['bid', 'ask'], 'greeks': ['delta', 'gamma', 'vega', 'theta'], 'iv': True},
        ],
        
        # ✅ Options filter for stock-opts-by-param
        'options_filter': {
            'selection_type': 'delta',
            'delta_from': 0.0,            # Wide range to match options-rawiv
            'delta_to': 1.0,              # Wide range to match options-rawiv
            'dte_tracking_min': 0,         # ✅ Track until expiration (0 DTE)
        },
    },
    'COVERED_CALL': {
        'name': 'Covered Call',
        'category': 'NEUTRAL',
        'risk_formula': 'max(stock_price * contracts * 100 - call_premium, stock_price * contracts * 100 * 0.8)',
        'required_fields': ['underlying_entry_price', 'contracts', 'total_cost'],
        'config_params': [
            {'key': 'stock_price', 'label': 'Stock Entry Price', 'format': '${:.2f}', 'in_summary': True},
            {'key': 'call_strike', 'label': 'Call Strike', 'format': '${:.0f}', 'in_summary': True},
            {'key': 'call_delta', 'label': 'Call Delta Target', 'format': '{:.2f}', 'in_summary': True},
            {'key': 'dte_target', 'label': 'DTE Target', 'format': '{:.0f} days', 'in_summary': True},
            {'key': 'position_size_pct', 'label': 'Position Size', 'format': '{:.1%} of capital', 'in_summary': True},
        ],
        'parameters': {
            'stock_price': {'label': 'Stock Price', 'format': '${:.2f}', 'csv': True, 'debug': True},
            'call_strike': {'label': 'Call Strike', 'format': '${:.0f}', 'csv': True, 'debug': True},
            'call_premium': {'label': 'Call Premium', 'format': '${:.2f}', 'csv': True, 'debug': True},
            'call_delta': {'label': 'Call Delta', 'format': '{:.3f}', 'csv': True, 'debug': True},
        },
        'file_naming': {
            'signature': ['stock_price', 'call_strike'],
            'format': [
                {'key': 'stock_price', 'code': 'S', 'formatter': lambda x: f"{x:.0f}"},
                {'key': 'call_strike', 'code': 'CS', 'formatter': lambda x: f"{int(x)}"},
                {'key': 'call_delta', 'code': 'D', 'formatter': lambda x: f"{int(x*100)}"},
                {'key': 'dte_target', 'code': 'DT', 'formatter': lambda x: f"{int(x)}"},
                {'key': 'position_size_pct', 'code': 'PS', 'formatter': lambda x: f"{x:.2f}".rstrip('0').rstrip('.')},
            ]
        },
        
        # Leg structure (for CSV export fields)
        'legs': [
            {'name': 'stock', 'fields': ['bid', 'ask', 'price'], 'greeks': [], 'iv': False},  # Stock has no greeks/IV
            {'name': 'call', 'fields': ['bid', 'ask'], 'greeks': ['delta', 'gamma', 'vega', 'theta'], 'iv': True},
        ],
        
        # Indicators (optional - for entry timing)
        'indicators': [
            {
                'name': 'realized_vol',
                'required': False,
                'params_from_config': ['lookback_period']  # lookback_period auto-calculated from lookback_ratio
            }
        ],
        
        # ✅ Options filter for stock-opts-by-param (OTM calls)
        'options_filter': {
            'selection_type': 'delta',
            'delta_from': 0.0,            # Wide range to match options-rawiv
            'delta_to': 1.0,              # Wide range to match options-rawiv
            'dte_tracking_min': 0,         # ✅ Track until expiration (0 DTE)
        },
    },
    'STRADDLE': {
        'name': 'Straddle',
        'category': 'NEUTRAL',
        'risk_formula': 'SHORT: premium * 2 | LONG: premium * 1.5',  # 📝 Documentation only (actual logic in calculate_risk)
        'required_fields': ['strike', 'total_cost'],
        'config_params': [
            {'key': 'dte_target', 'label': 'DTE Target', 'format': '{:.0f} days', 'in_summary': True},
            {'key': 'strike_selection', 'label': 'Strike Selection', 'format': '{}', 'in_summary': True},
            {'key': 'delta_target', 'label': 'Delta Target', 'format': '{:.2f}', 'in_summary': True},
            {'key': 'position_size_pct', 'label': 'Position Size', 'format': '{:.1%} of capital', 'in_summary': True},
        ],
        'parameters': {
            'strike': {'label': 'Strike', 'format': '${:.0f}', 'csv': True, 'debug': True},
        },
        'file_naming': {
            'signature': ['dte_target', 'strike_selection'],
            'format': [
                {'key': 'dte_target', 'code': 'DT', 'formatter': lambda x: f"{int(x)}"},
                {'key': 'strike_selection', 'code': '', 'formatter': lambda x: str(x)},
                {'key': 'delta_target', 'code': 'D', 'formatter': lambda x: f"{int(x*100)}"},
                {'key': 'position_size_pct', 'code': 'PS', 'formatter': lambda x: f"{x:.2f}".rstrip('0').rstrip('.')},
            ]
        },
        
        # Leg structure (for CSV export fields)
        'legs': [
            {'name': 'call', 'fields': ['bid', 'ask'], 'greeks': ['delta', 'gamma', 'vega', 'theta'], 'iv': True},
            {'name': 'put', 'fields': ['bid', 'ask'], 'greeks': ['delta', 'gamma', 'vega', 'theta'], 'iv': True},
        ],
        
        # Indicators (optional - for entry filtering based on volatility)
        'indicators': [
            {
                'name': 'vix_percentile',
                'required': False,
                'params_from_config': ['lookback_period']  # lookback_period auto-calculated from lookback_ratio
            },
            {
                'name': 'realized_vol',
                'required': False,
                'params_from_config': ['lookback_period']  # lookback_period auto-calculated from lookback_ratio
            },
            {
                'name': 'iv_rank_ivx',  # ✅ NEW: IVX-based IV Rank (faster alternative)
                'required': False,
                'params_from_config': []
            },
            {
                'name': 'iv_percentile_ivx',  # ✅ NEW: IVX-based IV Percentile
                'required': False,
                'params_from_config': []
            }
        ],
        
        # ✅ Options filter for stock-opts-by-param (full delta range for earnings moves)
        'options_filter': {
            'selection_type': 'delta',
            'delta_from': 0.0,             # Full range to capture ITM/OTM after big moves
            'delta_to': 1.0,
            'dte_tracking_min': 0,         # ✅ Track until expiration (0 DTE)
        },
    },
    'IV_LEAN': {
        'name': 'IV Lean (Z-Score Straddle)',
        'category': 'NEUTRAL',  # ✅ Can be SHORT (CREDIT) or LONG (DEBIT) - detected at runtime
        'risk_formula': 'SHORT: premium * 2 | LONG: premium * 1.5',  # 📝 Documentation only (actual logic in calculate_risk)
        'required_fields': ['total_cost'],
        'config_params': [
            {'key': 'z_score_entry', 'label': 'Z-Score Entry', 'format': '{:.1f}', 'in_summary': True},
            {'key': 'z_score_exit', 'label': 'Exit Threshold', 'format': '{:.2f}', 'in_summary': True},
            {'key': 'lookback_period', 'label': 'Lookback Period', 'format': '{:.0f} days', 'in_summary': True},
            {'key': 'dte_target', 'label': 'DTE Target', 'format': '{:.0f} days', 'in_summary': True},
            {'key': 'position_size_pct', 'label': 'Position Size', 'format': '{:.1%} of capital', 'in_summary': True},
        ],
        'parameters': {
            'strike': {'label': 'Strike', 'format': '${:.0f}', 'csv': True, 'debug': True},
            'z_score': {'label': 'Z-Score', 'format': '{:.2f}', 'csv': True, 'debug': True},
        },
        'file_naming': {
            # Signature: keys required to identify this strategy (use lookback_ratio OR lookback_period)
            'signature': ['z_score_entry', 'z_score_exit'],  # Removed lookback_period - it's auto-calculated
            'format': [
                {'key': 'z_score_entry', 'code': 'Z', 'formatter': lambda x: f"{x:.1f}"},
                {'key': 'z_score_exit', 'code': 'E', 'formatter': lambda x: f"{x:.2f}"},
                {'key': 'lookback_period', 'code': 'L', 'formatter': lambda x: f"{int(x)}"},  # Auto-calculated from lookback_ratio
                {'key': 'dte_target', 'code': 'DT', 'formatter': lambda x: f"{int(x)}"},
                {'key': 'position_size_pct', 'code': 'PS', 'formatter': lambda x: f"{x:.2f}".rstrip('0').rstrip('.')},
            ]
        },
        
        # Leg structure (for CSV export fields)
        'legs': [
            {'name': 'call', 'fields': ['bid', 'ask'], 'greeks': ['delta', 'gamma', 'vega', 'theta'], 'iv': True},
            {'name': 'put', 'fields': ['bid', 'ask'], 'greeks': ['delta', 'gamma', 'vega', 'theta'], 'iv': True},
        ],
        
        # Indicators (auto-detected from strategy_type)
        'indicators': [
            {
                'name': 'iv_lean_zscore_ivx',  # ✅ IVX-based (100x faster than raw options!)
                'required': True,  # ← PRIMARY indicator for IV_LEAN
                'params_from_config': ['lookback_period', 'dte_target'],
                'used_in_parameters': ['z_score']
            }
            # NOTE: Legacy 'iv_lean_zscore' removed (requires 'Adjusted close' column which is not available)
        ],
        
        # ✅ NEW: Options filter for stock-opts-by-param (20x less data!)
        'options_filter': {
            'selection_type': 'delta',      # ✅ FIXED: Delta now auto-inverts for Puts!
            'delta_from': 0.0,             # For Calls: 0.0 to 1.0 | For Puts: -1.0 to 0.0 (auto-inverted)
            'delta_to': 1.0,               # Wide range to catch deep OTM/ITM
            'dte_tracking_min': 0,          # ✅ Track until expiration (0 DTE) (not just entry range!)
        },
    },
    'STRANGLE': {
        'name': 'Strangle',
        'category': 'NEUTRAL',
        'risk_formula': 'SHORT: premium * 2 | LONG: premium * 1.5',  # 📝 Documentation only (actual logic in calculate_risk)
        'required_fields': ['total_cost'],
        'config_params': [
            {'key': 'call_delta', 'label': 'Call Delta Target', 'format': '{:.2f}', 'in_summary': True},
            {'key': 'put_delta', 'label': 'Put Delta Target', 'format': '{:.2f}', 'in_summary': True},
            {'key': 'dte_target', 'label': 'DTE Target', 'format': '{:.0f} days', 'in_summary': True},
            {'key': 'position_size_pct', 'label': 'Position Size', 'format': '{:.1%} of capital', 'in_summary': True},
        ],
        'parameters': {
            'call_strike': {'label': 'Call Strike', 'format': '${:.0f}', 'csv': True, 'debug': True},
            'put_strike': {'label': 'Put Strike', 'format': '${:.0f}', 'csv': True, 'debug': True},
        },
        'file_naming': {
            'signature': ['call_delta', 'put_delta'],
            'format': [
                {'key': 'call_delta', 'code': 'CD', 'formatter': lambda x: f"{int(x*100)}"},
                {'key': 'put_delta', 'code': 'PD', 'formatter': lambda x: f"{int(x*100)}"},
                {'key': 'dte_target', 'code': 'DT', 'formatter': lambda x: f"{int(x)}"},
                {'key': 'position_size_pct', 'code': 'PS', 'formatter': lambda x: f"{x:.2f}".rstrip('0').rstrip('.')},
            ]
        },
        
        # Leg structure (for CSV export fields)
        'legs': [
            {'name': 'call', 'fields': ['bid', 'ask'], 'greeks': ['delta', 'gamma', 'vega', 'theta'], 'iv': True},
            {'name': 'put', 'fields': ['bid', 'ask'], 'greeks': ['delta', 'gamma', 'vega', 'theta'], 'iv': True},
        ],
        
        # Indicators (optional - for entry filtering based on volatility)
        'indicators': [
            {
                'name': 'vix_percentile',
                'required': False,
                'params_from_config': ['lookback_period']  # lookback_period auto-calculated from lookback_ratio
            },
            {
                'name': 'realized_vol',
                'required': False,
                'params_from_config': ['lookback_period']  # lookback_period auto-calculated from lookback_ratio
            },
            {
                'name': 'iv_rank_ivx',  # ✅ NEW: IVX-based IV Rank (faster alternative)
                'required': False,
                'params_from_config': []
            },
            {
                'name': 'iv_percentile_ivx',  # ✅ NEW: IVX-based IV Percentile
                'required': False,
                'params_from_config': []
            }
        ],
        
        # ✅ Options filter for stock-opts-by-param (OTM delta-based)
        'options_filter': {
            'selection_type': 'delta',
            'delta_from': 0.0,            # Wide range to match options-rawiv
            'delta_to': 1.0,              # Wide range to match options-rawiv
            'dte_tracking_min': 0,         # ✅ Track until expiration (0 DTE)
        },
    },
}

# Backwards compatibility mapping (lowercase to UPPERCASE)
_STRATEGY_NAME_MAP = {
    'iron_condor': 'IRON_CONDOR',
    'straddle': 'STRADDLE',
    'strangle': 'STRANGLE',
    'credit_spread': 'CREDIT_SPREAD',
    'butterfly': 'BUTTERFLY',
    'calendar_spread': 'CALENDAR_SPREAD',
    'diagonal_spread': 'DIAGONAL_SPREAD',
    'iv_lean': 'IV_LEAN',  # iv_lean has its own strategy now (Z-score based)
}

# ============================================================================
# INDICATOR REGISTRY - Universal pre-calculation system
# ============================================================================

INDICATOR_REGISTRY = {
    'iv_lean_zscore': {
        'description': 'IV Lean Z-score (Call IV - Put IV normalized)',
        'inputs': ['options_df'],
        'required_params': ['lookback_period', 'dte_target', 'dte_tolerance'],
        'optional_params': {},
        'calculator': 'calculate_iv_lean_indicator',
        'outputs': ['date', 'iv_lean', 'mean_lean', 'std_lean', 'z_score'],
        'cache_key_params': ['lookback_period', 'dte_target', 'dte_tolerance']
    },
    
    'iv_rank': {
        'description': 'IV Rank (current IV position in historical range)',
        'inputs': ['options_df'],
        'required_params': ['lookback_period', 'dte_target'],  # lookback_period auto-calculated from lookback_ratio
        'optional_params': {},
        'calculator': 'calculate_iv_rank_indicator',
        'outputs': ['date', 'atm_iv', 'iv_rank', 'iv_high', 'iv_low'],
        'cache_key_params': ['lookback_period', 'dte_target']
    },
    
    'iv_rank_ivx': {
        'description': 'IV Rank from IVX data (calculated from rolling high/low)',
        'inputs': ['ivx_df'],  # ← Uses IVX data from /equities/eod/ivx
        'required_params': [],
        'optional_params': {
            'dte_target': None,       # If set, auto-selects closest tenor (e.g., 45 → '60d')
            'tenor': '30d',           # Tenor to use: '7d', '14d', '21d', '30d', '60d', '90d', '120d', '150d', '180d', '270d', '360d', '720d', '1080d'
            'lookback_period': 63     # Rolling window for IV High/Low (default: 63 days ≈ 3 months, optimized based on backtesting)
        },
        'calculator': 'calculate_iv_rank_from_ivx',
        'outputs': ['date', 'atm_iv', 'iv_rank', 'iv_high', 'iv_low'],
        'cache_key_params': ['tenor', 'lookback_period']  # Cache by tenor and lookback
    },
    
    'iv_lean_zscore_ivx': {
        'description': 'IV Lean Z-score from IVX data (faster than options_df)',
        'inputs': ['ivx_df'],  # ← Uses IVX data from /equities/eod/ivx
        'required_params': [],
        'optional_params': {
            'dte_target': 90,         # Target DTE (auto-selects closest tenor: 7, 14, 21, 30, 60, 90, 120, 150, 180, 270, 360, 720, 1080)
            'lookback_period': 60     # Rolling window for Z-score calculation (calendar days)
        },
        'calculator': 'calculate_iv_lean_from_ivx',
        'outputs': ['date', 'iv_lean', 'mean_lean', 'std_lean', 'z_score'],
        'cache_key_params': ['dte_target', 'lookback_period']
    },
    
    'iv_percentile_ivx': {
        'description': 'IV Percentile from IVX data (current IV position in historical range)',
        'inputs': ['ivx_df'],  # ← Uses IVX data from /equities/eod/ivx
        'required_params': [],
        'optional_params': {
            'dte_target': None,       # If set, auto-selects closest tenor (e.g., 45 → '60d')
            'tenor': '30d',           # Tenor to use: '7d', '14d', '21d', '30d', '60d', '90d', '120d', '150d', '180d', '270d', '360d', '720d', '1080d'
            'lookback_period': 63     # Rolling window for percentile calculation (default: 63 days ≈ 3 months, optimized based on backtesting)
        },
        'calculator': 'calculate_iv_percentile_from_ivx',
        'outputs': ['date', 'atm_iv', 'iv_percentile'],
        'cache_key_params': ['tenor', 'lookback_period']
    },
    
    'iv_term_structure': {
        'description': 'IV Term Structure (volatility curve shape across tenors)',
        'inputs': ['ivx_df'],  # ← Uses IVX data from /equities/eod/ivx
        'required_params': [],
        'optional_params': {},
        'calculator': 'calculate_iv_term_structure',
        'outputs': ['date', 'iv_30d', 'iv_60d', 'iv_90d', 'term_slope_30_60', 'term_slope_60_90', 'term_slope_30_90'],
        'cache_key_params': []  # No params - uses fixed tenors
    },
    
    'iv_skew': {
        'description': 'Put/Call IV Skew',
        'inputs': ['options_df'],
        'required_params': ['dte_target'],
        'optional_params': {'delta_otm': 0.25},
        'calculator': 'calculate_iv_skew_indicator',
        'outputs': ['date', 'put_iv', 'call_iv', 'skew'],
        'cache_key_params': ['dte_target', 'delta_otm']
    },
    
    'vix_percentile': {
        'description': 'VIX Percentile Rank',
        'inputs': ['vix_df'],
        'required_params': ['lookback_period'],  # lookback_period auto-calculated from lookback_ratio
        'optional_params': {},
        'calculator': 'calculate_vix_percentile_indicator',
        'outputs': ['date', 'vix', 'vix_percentile', 'vix_ma'],
        'cache_key_params': ['lookback_period']
    },
    
    'realized_vol': {
        'description': 'Realized Volatility (Historical)',
        'inputs': ['stock_df'],
        'required_params': ['lookback_period'],  # lookback_period auto-calculated from lookback_ratio
        'optional_params': {'annualize': True},
        'calculator': 'calculate_realized_vol_indicator',
        'outputs': ['date', 'close', 'realized_vol', 'rv_ma'],
        'cache_key_params': ['lookback_period']
    },
    
    'rsi': {
        'description': 'Relative Strength Index',
        'inputs': ['stock_df'],
        'required_params': [],
        'optional_params': {},  # lookback_period auto-calculated from lookback_ratio
        'calculator': 'calculate_rsi_indicator',
        'outputs': ['date', 'close', 'rsi', 'rsi_ma'],
        'cache_key_params': ['lookback_period']
    },
    
    'atr': {
        'description': 'Average True Range',
        'inputs': ['stock_df'],
        'required_params': [],
        'optional_params': {},  # lookback_period auto-calculated from lookback_ratio
        'calculator': 'calculate_atr_indicator',
        'outputs': ['date', 'close', 'atr', 'atr_pct'],
        'cache_key_params': ['lookback_period']
    },
    
    'bollinger': {
        'description': 'Bollinger Bands',
        'inputs': ['stock_df'],
        'required_params': [],
        'optional_params': {'num_std': 2},  # lookback_period auto-calculated by ratio (default: 1.0)
        'calculator': 'calculate_bollinger_indicator',
        'outputs': ['date', 'close', 'bb_middle', 'bb_upper', 'bb_lower', 'bb_width', 'bb_position'],
        'cache_key_params': ['lookback_period', 'num_std']
    },
    
    'macd': {
        'description': 'MACD (Moving Average Convergence Divergence)',
        'inputs': ['stock_df'],
        'required_params': [],
        'optional_params': {'fast_period': 12, 'slow_period': 26, 'signal_period': 9},
        'calculator': 'calculate_macd_indicator',
        'outputs': ['date', 'close', 'macd', 'macd_signal', 'macd_hist'],
        'cache_key_params': ['fast_period', 'slow_period', 'signal_period']
    },
    
    'expected_move': {
        'description': 'Expected Move (from ATM straddle)',
        'inputs': ['options_df', 'stock_df'],
        'required_params': ['dte_target', 'dte_tolerance'],
        'optional_params': {},
        'calculator': 'calculate_expected_move_indicator',
        'outputs': ['date', 'close', 'atm_straddle_price', 'expected_move', 'expected_move_pct'],
        'cache_key_params': ['dte_target', 'dte_tolerance']
    },
    
    'put_call_ratio': {
        'description': 'Put/Call Volume Ratio',
        'inputs': ['options_df'],
        'required_params': ['dte_target', 'dte_tolerance'],
        'optional_params': {},
        'calculator': 'calculate_put_call_ratio_indicator',
        'outputs': ['date', 'put_volume', 'call_volume', 'pcr', 'pcr_ma'],
        'cache_key_params': ['dte_target', 'dte_tolerance']
    },
    
    'hv_iv_ratio': {
        'description': 'Historical Volatility / Implied Volatility Ratio',
        'inputs': ['stock_df', 'options_df'],
        'required_params': ['dte_target', 'dte_tolerance'],
        'optional_params': {'hv_lookback': 30},
        'calculator': 'calculate_hv_iv_ratio_indicator',
        'outputs': ['date', 'close', 'hv', 'atm_iv', 'hv_iv_ratio'],
        'cache_key_params': ['hv_lookback', 'dte_target', 'dte_tolerance']
    },
}

# ============================================================================
# INDICATOR CALCULATOR FUNCTIONS - Vectorized implementations
# ============================================================================

def calculate_iv_lean_indicator(options_df, lookback_period, dte_target, dte_tolerance):
    """
    Calculate IV Lean Z-score timeseries (CORRECT LOGIC - matches original)
    
    CRITICAL: Uses CALENDAR DAYS lookback, not # of records!
    
    Args:
        options_df: Options data with columns ['date', 'strike', 'expiration', 'Call/Put', 'iv', 'Adjusted close']
        lookback_period: Lookback in CALENDAR DAYS (e.g., 60 days back)
        dte_target: Target DTE (e.g., 30, 45, 90)
        dte_tolerance: Tolerance around DTE (e.g., 7, 10, 20) - from config
    
    Returns:
        pd.DataFrame with columns: ['date', 'iv_lean', 'mean_lean', 'std_lean', 'z_score']
    """
    import pandas as pd
    import numpy as np
    
    trading_dates = sorted(options_df['date'].unique())
    
    # Step 1: Calculate IV Lean for ALL dates
    lean_history = {}
    for current_date in trading_dates:
        day_data = options_df[options_df['date'] == current_date]
        if day_data.empty:
            continue
        
        stock_price = float(day_data['Adjusted close'].iloc[0])
        
        # Filter by DTE
        dte_filtered = day_data[
            (day_data['dte'] >= dte_target - dte_tolerance) & 
            (day_data['dte'] <= dte_target + dte_tolerance)
        ]
        
        if dte_filtered.empty:
            continue
        
        # Find ATM strike
        dte_filtered = dte_filtered.copy()
        dte_filtered['strike_diff'] = abs(dte_filtered['strike'] - stock_price)
        atm_idx = dte_filtered['strike_diff'].idxmin()
        atm_strike = float(dte_filtered.loc[atm_idx, 'strike'])
        
        # Get ATM call/put IVs
        atm_options = dte_filtered[dte_filtered['strike'] == atm_strike]
        atm_call = atm_options[atm_options['type'] == 'C']
        atm_put = atm_options[atm_options['type'] == 'P']
        
        if not atm_call.empty and not atm_put.empty:
            call_iv = float(atm_call['iv'].iloc[0])
            put_iv = float(atm_put['iv'].iloc[0])
            
            if pd.notna(call_iv) and pd.notna(put_iv) and call_iv > 0 and put_iv > 0:
                lean_history[current_date] = call_iv - put_iv
    
    if not lean_history:
        return pd.DataFrame()
    
    # Step 2: ✅ CORRECTED: Calculate rolling mean/std using CALENDAR DAYS, not records!
    results = []
    for current_date in trading_dates:
        if current_date not in lean_history:
            continue
        
        # ✅ CRITICAL: Lookback by CALENDAR DAYS (matches original logic!)
        lookback_start = current_date - pd.Timedelta(days=lookback_period)
        
        # Get all lean values in the lookback window (UP TO current_date)
        historical_leans = [
            lean for date, lean in lean_history.items()
            if lookback_start <= date <= current_date
        ]
        
        # ✅ CRITICAL: Require minimum 10 data points (matches original!)
        if len(historical_leans) < 10:
            continue
        
        mean_lean = np.mean(historical_leans)
        std_lean = np.std(historical_leans)
        
        if std_lean == 0:
            continue
        
        current_lean = lean_history[current_date]
        z_score = (current_lean - mean_lean) / std_lean
        
        results.append({
            'date': current_date,
            'iv_lean': current_lean,
            'mean_lean': mean_lean,
            'std_lean': std_lean,
            'z_score': z_score
        })
    
    return pd.DataFrame(results)


def calculate_iv_lean_from_ivx(ivx_df, dte_target=90, lookback_period=60, symbol=None):
    """
    Calculate IV Lean from IVX endpoint (simplified, faster approach)
    
    Uses pre-calculated IVX tenors (7d, 14d, 21d, 30d, 60d, 90d, 120d, 150d, 180d, 270d, 360d, 720d, 1080d)
    which are already normalized and weighted by Delta/Vega across 8 ATM options.
    
    Args:
        ivx_df: IVX data from /equities/eod/ivx endpoint
                Must have columns: 'date', '{tenor}d IV Call', '{tenor}d IV Put'
        dte_target: Target DTE (will use closest available tenor)
                   Available: 7, 14, 21, 30, 60, 90, 120, 150, 180, 270, 360, 720, 1080
        lookback_period: Lookback in calendar days for rolling statistics
        symbol: Optional symbol to include in output DataFrame (for multi-symbol support)
    
    Returns:
        pd.DataFrame with columns: ['date', 'symbol', 'iv_lean', 'mean_lean', 'std_lean', 'z_score']
                                   (symbol column included if provided)
    
    Example:
        >>> ivx_data = api_call('/equities/eod/ivx', symbol='SPY', from_='2024-01-01', to='2024-12-31')
        >>> ivx_df = pd.DataFrame(ivx_data['data'])
        >>> lean_df = calculate_iv_lean_from_ivx(ivx_df, dte_target=90, lookback_period=60, symbol='SPY')
        >>> print(lean_df[['date', 'symbol', 'iv_lean', 'z_score']].tail())
    """
    import pandas as pd
    import numpy as np
    
    # Map DTE to IVX column names (available tenors from API)
    TENOR_MAP = {
        7: '7d', 14: '14d', 21: '21d', 30: '30d',
        60: '60d', 90: '90d', 120: '120d', 150: '150d',
        180: '180d', 270: '270d', 360: '360d', 720: '720d', 1080: '1080d'
    }
    
    # Find closest available tenor
    if dte_target not in TENOR_MAP:
        closest_dte = min(TENOR_MAP.keys(), key=lambda x: abs(x - dte_target))
        print(f"⚠️  Warning: DTE {dte_target} not available in IVX. Using closest tenor: {closest_dte}d")
        dte_target = closest_dte
    
    tenor = TENOR_MAP[dte_target]
    call_col = f'{tenor} IV Call'
    put_col = f'{tenor} IV Put'
    
    # Validate required columns exist
    if call_col not in ivx_df.columns or put_col not in ivx_df.columns:
        available_tenors = [k for k, v in TENOR_MAP.items() 
                           if f'{v} IV Call' in ivx_df.columns]
        raise ValueError(
            f"IVX data missing required columns: '{call_col}' or '{put_col}'\n"
            f"Available tenors in data: {available_tenors}\n"
            f"Required columns: {list(ivx_df.columns)}"
        )
    
    # Ensure 'date' column is datetime
    ivx_df = ivx_df.copy()
    if not pd.api.types.is_datetime64_any_dtype(ivx_df['date']):
        ivx_df['date'] = pd.to_datetime(ivx_df['date'])
    
    # Check if multi-symbol data (consistent with other IVX calculators)
    has_symbol = 'symbol' in ivx_df.columns
    
    # Step 1: Calculate IV Lean (one line!)
    ivx_df['iv_lean'] = ivx_df[call_col] - ivx_df[put_col]
    
    # Remove rows with NaN IV values
    ivx_df = ivx_df.dropna(subset=['iv_lean'])
    
    if ivx_df.empty:
        cols = ['date', 'iv_lean', 'mean_lean', 'std_lean', 'z_score']
        if has_symbol:
            cols.insert(1, 'symbol')  # Insert symbol after date
        return pd.DataFrame(columns=cols)
    
    # Sort by date
    ivx_df = ivx_df.sort_values('date').reset_index(drop=True)
    
    # Step 2: Rolling statistics (same logic as original function)
    results = []
    
    for idx, row in ivx_df.iterrows():
        current_date = row['date']
        
        # Calculate lookback window using CALENDAR DAYS (matches original logic)
        lookback_start = current_date - pd.Timedelta(days=lookback_period)
        
        # Get all lean values in the lookback window (UP TO current_date)
        historical = ivx_df[
            (ivx_df['date'] >= lookback_start) &
            (ivx_df['date'] <= current_date)
        ]
        
        # Require minimum 10 data points (matches original function)
        if len(historical) < 10:
            continue
        
        mean_lean = historical['iv_lean'].mean()
        std_lean = historical['iv_lean'].std()
        
        # Skip if no variation (std = 0)
        if std_lean == 0 or pd.isna(std_lean):
            continue
        
        current_lean = row['iv_lean']
        z_score = (current_lean - mean_lean) / std_lean
        
        result_row = {
            'date': current_date,
            'iv_lean': current_lean,
            'mean_lean': mean_lean,
            'std_lean': std_lean,
            'z_score': z_score
        }
        
        # ✅ FIX: Include symbol from DataFrame if present (consistent with other IVX calculators)
        if has_symbol:
            result_row['symbol'] = row['symbol']
        
        results.append(result_row)
    
    return pd.DataFrame(results)


def preload_ivx_zscore_cache(config, cache_config=None):
    """
    Pre-calculate Z-scores from IVX data for the entire backtest period.
    
    This function loads IVX data and calculates IV Lean Z-scores upfront,
    creating a lookup dict for fast access during backtest.
    
    Args:
        config: Backtest config with 'symbol', 'start_date', 'end_date', 
                'dte_target', 'lookback_period' (or 'lookback_ratio')
        cache_config: Optional cache configuration
    
    Returns:
        dict: {date: {'z_score': float, 'current_lean': float, 'mean_lean': float, 'std_lean': float}}
    
    Example:
        >>> z_cache = preload_ivx_zscore_cache(config)
        >>> z_data = z_cache.get(current_date, {})
        >>> z_score = z_data.get('z_score')
    """
    import pandas as pd
    from datetime import datetime, timedelta
    
    symbol = config['symbol']
    start_date = pd.to_datetime(config['start_date'])
    end_date = pd.to_datetime(config['end_date'])
    dte_target = config.get('dte_target', 90)
    
    # Get lookback_period from config (or calculate from lookback_ratio)
    lookback_period = config.get('lookback_period')
    if lookback_period is None:
        lookback_ratio = config.get('lookback_ratio', 0.25)
        total_days = (end_date - start_date).days
        lookback_period = int(total_days * lookback_ratio)
        print(f"[preload_ivx_zscore_cache] Calculated lookback_period={lookback_period} from ratio={lookback_ratio}")
    
    # Extend start date to include lookback period for accurate Z-scores
    extended_start = start_date - timedelta(days=lookback_period + 30)
    
    print(f"[preload_ivx_zscore_cache] Loading IVX data for {symbol}...")
    print(f"   Period: {extended_start.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print(f"   DTE target: {dte_target}, Lookback: {lookback_period} days")
    
    # Load IVX data
    ivx_response = api_call(
        '/equities/eod/ivx',
        cache_config,
        symbol=symbol,
        from_=extended_start.strftime('%Y-%m-%d'),
        to=end_date.strftime('%Y-%m-%d')
    )
    
    if not ivx_response or 'data' not in ivx_response or len(ivx_response['data']) == 0:
        print(f"⚠️  [preload_ivx_zscore_cache] No IVX data found!")
        return {}
    
    ivx_df = pd.DataFrame(ivx_response['data'])
    print(f"   Loaded {len(ivx_df)} IVX records")
    
    # Calculate Z-scores
    lean_df = calculate_iv_lean_from_ivx(ivx_df, dte_target=dte_target, lookback_period=lookback_period)
    
    if lean_df.empty:
        print(f"⚠️  [preload_ivx_zscore_cache] No Z-scores calculated!")
        return {}
    
    print(f"   Calculated {len(lean_df)} Z-score values")
    
    # Build lookup dict
    z_cache = {}
    for _, row in lean_df.iterrows():
        # ✅ FIX: Convert to datetime.date for consistency with trading_days
        date = pd.to_datetime(row['date']).date()
        z_cache[date] = {
            'z_score': row['z_score'],
            'current_lean': row['iv_lean'],
            'mean_lean': row['mean_lean'],
            'std_lean': row['std_lean']
        }
    
    print(f"✅ [preload_ivx_zscore_cache] Cache ready: {len(z_cache)} dates")
    
    return z_cache


def calculate_iv_rank_indicator(options_df, lookback_period, dte_target):
    """
    Calculate IV Rank timeseries (VECTORIZED!)
    Supports MULTI-SYMBOL data (if 'symbol' column present)
    
    Args:
        options_df: Options data
        lookback_period: Window for high/low (e.g., 30, 60)
        dte_target: Target DTE
    
    Returns:
        pd.DataFrame with columns: ['date', 'symbol', 'atm_iv', 'iv_rank', 'iv_high', 'iv_low']
    """
    import pandas as pd
    import numpy as np
    
    # Check if multi-symbol data
    has_symbol = 'symbol' in options_df.columns
    
    if has_symbol:
        # Process each symbol separately
        all_results = []
        for symbol in options_df['symbol'].unique():
            symbol_df = options_df[options_df['symbol'] == symbol]
            symbol_result = _calculate_iv_rank_single_symbol(symbol_df, lookback_period, dte_target)
            if not symbol_result.empty:
                symbol_result['symbol'] = symbol
                all_results.append(symbol_result)
        
        if all_results:
            return pd.concat(all_results, ignore_index=True)
        else:
            return pd.DataFrame()
    else:
        # Single symbol
        return _calculate_iv_rank_single_symbol(options_df, lookback_period, dte_target)


def _calculate_iv_rank_single_symbol(options_df, lookback_period, dte_target):
    """Helper function to calculate IV Rank for a single symbol"""
    import pandas as pd
    import numpy as np  # Needed for np.where
    
    trading_dates = sorted(options_df['date'].unique())
    iv_history = []
    
    # Extract ATM IV for each date
    for current_date in trading_dates:
        day_data = options_df[options_df['date'] == current_date]
        if day_data.empty:
            continue
        
        stock_price = float(day_data['Adjusted close'].iloc[0])
        
        # Filter by DTE
        dte_filtered = day_data[
            (day_data['dte'] >= dte_target - 7) & 
            (day_data['dte'] <= dte_target + 7)
        ]
        
        if dte_filtered.empty:
            continue
        
        # Find ATM strike
        dte_filtered = dte_filtered.copy()
        dte_filtered['strike_diff'] = abs(dte_filtered['strike'] - stock_price)
        atm_idx = dte_filtered['strike_diff'].idxmin()
        atm_strike = float(dte_filtered.loc[atm_idx, 'strike'])
        
        # Get ATM IV (average of call and put)
        atm_options = dte_filtered[dte_filtered['strike'] == atm_strike]
        atm_call = atm_options[atm_options['type'] == 'C']
        atm_put = atm_options[atm_options['type'] == 'P']
        
        if not atm_call.empty and not atm_put.empty:
            call_iv = float(atm_call['iv'].iloc[0])
            put_iv = float(atm_put['iv'].iloc[0])
            
            if pd.notna(call_iv) and pd.notna(put_iv):
                atm_iv = (call_iv + put_iv) / 2
                iv_history.append({
                    'date': current_date,
                    'atm_iv': atm_iv
                })
    
    if not iv_history:
        return pd.DataFrame()
    
    # ✅ VECTORIZED: Rolling high/low
    iv_df = pd.DataFrame(iv_history).sort_values('date').reset_index(drop=True)
    
    # Use at least 50% of lookback_period as min_periods (more reliable)
    min_periods_required = max(lookback_period // 2, 30)
    
    iv_df['iv_high'] = iv_df['atm_iv'].rolling(window=lookback_period, min_periods=min_periods_required).max()
    iv_df['iv_low'] = iv_df['atm_iv'].rolling(window=lookback_period, min_periods=min_periods_required).min()
    
    # IV Rank calculation
    # Avoid division by zero when high == low
    iv_range = iv_df['iv_high'] - iv_df['iv_low']
    iv_df['iv_rank'] = np.where(
        iv_range > 0.001,  # Minimum range threshold
        ((iv_df['atm_iv'] - iv_df['iv_low']) / iv_range) * 100,
        50.0  # Default when range is too small or missing
    )
    
    return iv_df


def calculate_iv_rank_from_ivx(ivx_df, dte_target=None, tenor='30d', lookback_period=63, symbol=None):
    """
    Calculate IV Rank from IVX data
    
    IVX API provides multiple tenors (7d, 14d, 21d, 30d, 60d, 90d, 120d, 150d, 180d, 270d, 360d, 720d, 1080d).
    We select one tenor (default: 30d) and calculate IV Rank using rolling high/low over lookback_period.
    
    Args:
        ivx_df: IVX data with columns ['date', '{tenor} IV Mean', '{tenor} IV Call', '{tenor} IV Put', ...]
        dte_target: If provided, automatically select closest tenor (e.g., dte_target=45 → '60d')
        tenor: Tenor to use for IV calculation (default: '30d'). Options: '7d', '14d', '21d', '30d', '60d', '90d', '120d', '150d', '180d', '270d', '360d', '720d', '1080d'
        lookback_period: Rolling window for IV High/Low calculation (default: 63 days ≈ 3 months, optimized)
    
    Returns:
        pd.DataFrame with columns: ['date', 'symbol', 'atm_iv', 'iv_rank', 'iv_high', 'iv_low']
    """
    import pandas as pd
    import numpy as np
    
    if ivx_df.empty:
        return pd.DataFrame()
    
    # ✅ Auto-select tenor based on dte_target
    if dte_target:
        available_tenors = [7, 14, 21, 30, 60, 90, 120, 150, 180, 270, 360, 720, 1080]
        closest_tenor = min(available_tenors, key=lambda x: abs(x - dte_target))
        tenor = f'{closest_tenor}d'
    
    # Check if multi-symbol data
    has_symbol = 'symbol' in ivx_df.columns
    
    # ✅ Build column name for the selected tenor
    iv_mean_col = f'{tenor} IV Mean'
    
    if iv_mean_col not in ivx_df.columns:
        print(f"\n     ❌ Column '{iv_mean_col}' not found in IVX data!")
        print(f"     Available columns: {list(ivx_df.columns)}")
        return pd.DataFrame()
    
    # ✅ Ensure data is sorted by date
    ivx_df = ivx_df.sort_values('date').reset_index(drop=True)
    
    # ✅ Calculate rolling High/Low
    if has_symbol:
        # Multi-symbol: group by symbol first
        ivx_df['iv_high'] = ivx_df.groupby('symbol')[iv_mean_col].transform(
            lambda x: x.rolling(window=lookback_period, min_periods=1).max()
        )
        ivx_df['iv_low'] = ivx_df.groupby('symbol')[iv_mean_col].transform(
            lambda x: x.rolling(window=lookback_period, min_periods=1).min()
        )
    else:
        # Single symbol: direct rolling
        ivx_df['iv_high'] = ivx_df[iv_mean_col].rolling(window=lookback_period, min_periods=1).max()
        ivx_df['iv_low'] = ivx_df[iv_mean_col].rolling(window=lookback_period, min_periods=1).min()
    
    # ✅ Calculate IV Rank: (Current - Low) / (High - Low) * 100
    ivx_df['iv_rank'] = np.where(
        ivx_df['iv_high'] > ivx_df['iv_low'],
        ((ivx_df[iv_mean_col] - ivx_df['iv_low']) / (ivx_df['iv_high'] - ivx_df['iv_low'])) * 100,
        50.0  # Default to 50% if high == low
    )
    
    # ✅ Build result DataFrame
    result_cols = ['date']
    if has_symbol:
        result_cols.append('symbol')
    
    result_df = ivx_df[result_cols].copy()
    result_df['atm_iv'] = ivx_df[iv_mean_col]
    result_df['iv_rank'] = ivx_df['iv_rank']
    result_df['iv_high'] = ivx_df['iv_high']
    result_df['iv_low'] = ivx_df['iv_low']
    
    # Drop rows with NaN values
    result_df = result_df.dropna()
    
    return result_df


def calculate_iv_percentile_from_ivx(ivx_df, dte_target=None, tenor='30d', lookback_period=63, symbol=None):
    """
    Calculate IV Percentile from IVX data (current IV position in historical range)
    
    Similar to iv_rank_ivx, but returns percentile (0-100) instead of rank.
    Percentile shows what % of historical values are below current IV.
    
    Args:
        ivx_df: IVX data with columns ['date', '{tenor} IV Mean', ...]
        dte_target: If provided, automatically select closest tenor (e.g., dte_target=45 → '60d')
        tenor: Tenor to use for IV calculation (default: '30d'). Options: '7d', '14d', '21d', '30d', '60d', '90d', '120d', '150d', '180d', '270d', '360d', '720d', '1080d'
        lookback_period: Rolling window for percentile calculation (default: 63 days ≈ 3 months, optimized)
    
    Returns:
        pd.DataFrame with columns: ['date', 'symbol', 'atm_iv', 'iv_percentile']
    """
    import pandas as pd
    import numpy as np
    
    if ivx_df.empty:
        return pd.DataFrame()
    
    # ✅ Auto-select tenor based on dte_target
    if dte_target:
        available_tenors = [7, 14, 21, 30, 60, 90, 120, 150, 180, 270, 360, 720, 1080]
        closest_tenor = min(available_tenors, key=lambda x: abs(x - dte_target))
        tenor = f'{closest_tenor}d'
    
    # Check if multi-symbol data
    has_symbol = 'symbol' in ivx_df.columns
    
    # ✅ Build column name for the selected tenor
    iv_mean_col = f'{tenor} IV Mean'
    
    if iv_mean_col not in ivx_df.columns:
        print(f"\n     ❌ Column '{iv_mean_col}' not found in IVX data!")
        print(f"     Available columns: {list(ivx_df.columns)}")
        return pd.DataFrame()
    
    # ✅ Ensure data is sorted by date
    ivx_df = ivx_df.sort_values('date').reset_index(drop=True)
    
    # ✅ Calculate rolling percentile
    def calc_percentile(series):
        """Calculate percentile for each value in rolling window"""
        percentiles = []
        for i in range(len(series)):
            start = max(0, i - lookback_period + 1)
            window = series.iloc[start:i+1]
            if len(window) < 10:  # Require minimum 10 data points
                percentiles.append(np.nan)
            else:
                current = series.iloc[i]
                percentile = (window < current).sum() / len(window) * 100
                percentiles.append(percentile)
        return pd.Series(percentiles, index=series.index)
    
    if has_symbol:
        # Multi-symbol: group by symbol first
        ivx_df['iv_percentile'] = ivx_df.groupby('symbol')[iv_mean_col].transform(calc_percentile)
    else:
        # Single symbol: direct calculation
        ivx_df['iv_percentile'] = calc_percentile(ivx_df[iv_mean_col])
    
    # ✅ Build result DataFrame
    result_cols = ['date']
    if has_symbol:
        result_cols.append('symbol')
    
    result_df = ivx_df[result_cols].copy()
    result_df['atm_iv'] = ivx_df[iv_mean_col]
    result_df['iv_percentile'] = ivx_df['iv_percentile']
    
    # Drop rows with NaN values
    result_df = result_df.dropna()
    
    return result_df


def calculate_iv_term_structure(ivx_df, symbol=None):
    """
    Calculate IV Term Structure (volatility curve shape across tenors)
    
    Analyzes the shape of the IV curve by comparing short-term vs long-term volatility.
    Useful for identifying:
    - Contango: term_slope > 0 (normal: longer-term IV > short-term IV)
    - Backwardation: term_slope < 0 (stress: short-term IV > longer-term IV)
    
    Args:
        ivx_df: IVX data with columns ['date', '30d IV Mean', '60d IV Mean', '90d IV Mean', ...]
    
    Returns:
        pd.DataFrame with columns: ['date', 'symbol', 'iv_30d', 'iv_60d', 'iv_90d', 
                                    'term_slope_30_60', 'term_slope_60_90', 'term_slope_30_90']
    """
    import pandas as pd
    import numpy as np
    
    if ivx_df.empty:
        return pd.DataFrame()
    
    # Check if multi-symbol data
    has_symbol = 'symbol' in ivx_df.columns
    
    # Required columns
    required_cols = ['30d IV Mean', '60d IV Mean', '90d IV Mean']
    missing_cols = [col for col in required_cols if col not in ivx_df.columns]
    
    if missing_cols:
        print(f"\n     ❌ Missing required columns for term structure: {missing_cols}")
        print(f"     Available columns: {list(ivx_df.columns)}")
        return pd.DataFrame()
    
    # ✅ Build result DataFrame
    result_cols = ['date']
    if has_symbol:
        result_cols.append('symbol')
    
    result_df = ivx_df[result_cols].copy()
    result_df['iv_30d'] = ivx_df['30d IV Mean']
    result_df['iv_60d'] = ivx_df['60d IV Mean']
    result_df['iv_90d'] = ivx_df['90d IV Mean']
    
    # ✅ Calculate term structure slopes
    result_df['term_slope_30_60'] = result_df['iv_60d'] - result_df['iv_30d']
    result_df['term_slope_60_90'] = result_df['iv_90d'] - result_df['iv_60d']
    result_df['term_slope_30_90'] = result_df['iv_90d'] - result_df['iv_30d']
    
    # Drop rows with NaN values
    result_df = result_df.dropna()
    
    return result_df


def calculate_iv_skew_indicator(options_df, dte_target, delta_otm=0.25):
    """
    Calculate Put/Call IV Skew timeseries
    
    Args:
        options_df: Options data
        dte_target: Target DTE
        delta_otm: OTM delta to use (e.g., 0.25 = 25 delta)
    
    Returns:
        pd.DataFrame with columns: ['date', 'put_iv', 'call_iv', 'skew']
    """
    import pandas as pd
    import numpy as np
    
    trading_dates = sorted(options_df['date'].unique())
    skew_history = []
    
    for current_date in trading_dates:
        day_data = options_df[options_df['date'] == current_date]
        if day_data.empty:
            continue
        
        # Filter by DTE
        dte_filtered = day_data[
            (day_data['dte'] >= dte_target - 7) & 
            (day_data['dte'] <= dte_target + 7)
        ]
        
        if dte_filtered.empty:
            continue
        
        # Find OTM put and call closest to target delta
        puts = dte_filtered[dte_filtered['type'] == 'P']
        calls = dte_filtered[dte_filtered['type'] == 'C']
        
        if not puts.empty and not calls.empty and 'delta' in puts.columns:
            # Find 25 delta put (negative delta ~ -0.25)
            puts['delta_diff'] = abs(puts['delta'] + delta_otm)
            put_idx = puts['delta_diff'].idxmin()
            put_iv = float(puts.loc[put_idx, 'iv'])
            
            # Find 25 delta call (positive delta ~ 0.25)
            calls['delta_diff'] = abs(calls['delta'] - delta_otm)
            call_idx = calls['delta_diff'].idxmin()
            call_iv = float(calls.loc[call_idx, 'iv'])
            
            if pd.notna(put_iv) and pd.notna(call_iv):
                skew_history.append({
                    'date': current_date,
                    'put_iv': put_iv,
                    'call_iv': call_iv,
                    'skew': put_iv - call_iv  # Positive = puts more expensive
                })
    
    if not skew_history:
        return pd.DataFrame()
    
    return pd.DataFrame(skew_history)


def calculate_vix_percentile_indicator(vix_df, lookback_period=252):
    """
    Calculate VIX percentile timeseries (VECTORIZED!)
    
    Args:
        vix_df: VIX data with columns ['date', 'close']
        lookback_period: Window for percentile (e.g., 252 = 1 year)
    
    Returns:
        pd.DataFrame with columns: ['date', 'vix', 'vix_percentile', 'vix_ma']
    """
    import pandas as pd
    import numpy as np
    
    df = vix_df[['date', 'close']].copy().rename(columns={'close': 'vix'})
    df = df.sort_values('date').reset_index(drop=True)
    
    # ✅ VECTORIZED: Rolling percentile
    df['vix_percentile'] = df['vix'].rolling(window=lookback_period, min_periods=20).apply(
        lambda x: (x.iloc[-1] <= x).sum() / len(x) * 100, raw=False
    )
    
    df['vix_ma'] = df['vix'].rolling(window=lookback_period, min_periods=20).mean()
    
    return df


def calculate_realized_vol_indicator(stock_df, lookback_period=30, annualize=True):
    """
    Calculate Realized Volatility timeseries (VECTORIZED!)
    
    Args:
        stock_df: Stock data with columns ['date', 'close']
        lookback_period: Window for vol calculation (e.g., 30, 60)
        annualize: If True, annualize the volatility
    
    Returns:
        pd.DataFrame with columns: ['date', 'close', 'realized_vol', 'rv_ma']
    """
    import pandas as pd
    import numpy as np
    
    df = stock_df[['date', 'close']].copy()
    df = df.sort_values('date').reset_index(drop=True)
    
    # Calculate returns
    df['returns'] = df['close'].pct_change()
    
    # ✅ VECTORIZED: Rolling std
    df['realized_vol'] = df['returns'].rolling(window=lookback_period, min_periods=10).std()
    
    if annualize:
        df['realized_vol'] = df['realized_vol'] * np.sqrt(252) * 100  # Annualized %
    else:
        df['realized_vol'] = df['realized_vol'] * 100  # As %
    
    df['rv_ma'] = df['realized_vol'].rolling(window=lookback_period, min_periods=10).mean()
    
    return df[['date', 'close', 'realized_vol', 'rv_ma']]


def calculate_rsi_indicator(stock_df, lookback_period=14):
    """
    Calculate RSI timeseries (VECTORIZED!)
    
    Args:
        stock_df: Stock data with columns ['date', 'close']
        lookback_period: RSI period (e.g., 14)
    
    Returns:
        pd.DataFrame with columns: ['date', 'close', 'rsi', 'rsi_ma']
    """
    import pandas as pd
    import numpy as np
    
    df = stock_df[['date', 'close']].copy()
    df = df.sort_values('date').reset_index(drop=True)
    
    # Calculate price changes
    df['price_change'] = df['close'].diff()
    df['gain'] = df['price_change'].apply(lambda x: x if x > 0 else 0)
    df['loss'] = df['price_change'].apply(lambda x: -x if x < 0 else 0)
    
    # ✅ VECTORIZED: Rolling average gain/loss
    df['avg_gain'] = df['gain'].rolling(window=lookback_period, min_periods=5).mean()
    df['avg_loss'] = df['loss'].rolling(window=lookback_period, min_periods=5).mean()
    
    # RSI calculation
    df['rs'] = df['avg_gain'] / df['avg_loss'].replace(0, 1e-10)
    df['rsi'] = 100 - (100 / (1 + df['rs']))
    
    # RSI moving average
    df['rsi_ma'] = df['rsi'].rolling(window=lookback_period).mean()
    
    return df[['date', 'close', 'rsi', 'rsi_ma']]


def calculate_atr_indicator(stock_df, lookback_period=14):
    """
    Calculate ATR (Average True Range) timeseries (VECTORIZED!)
    
    Args:
        stock_df: Stock data with columns ['date', 'high', 'low', 'close']
        lookback_period: ATR period (e.g., 14)
    
    Returns:
        pd.DataFrame with columns: ['date', 'close', 'atr', 'atr_pct']
    """
    import pandas as pd
    import numpy as np
    
    df = stock_df[['date', 'high', 'low', 'close']].copy()
    df = df.sort_values('date').reset_index(drop=True)
    
    # True Range = max(high-low, abs(high-prev_close), abs(low-prev_close))
    df['prev_close'] = df['close'].shift(1)
    df['tr1'] = df['high'] - df['low']
    df['tr2'] = abs(df['high'] - df['prev_close'])
    df['tr3'] = abs(df['low'] - df['prev_close'])
    df['tr'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
    
    # ✅ VECTORIZED: ATR = rolling mean of TR
    df['atr'] = df['tr'].rolling(window=lookback_period, min_periods=5).mean()
    df['atr_pct'] = (df['atr'] / df['close']) * 100  # ATR as % of price
    
    return df[['date', 'close', 'atr', 'atr_pct']]


def calculate_bollinger_indicator(stock_df, lookback_period=20, num_std=2):
    """
    Calculate Bollinger Bands timeseries (VECTORIZED!)
    
    Args:
        stock_df: Stock data with columns ['date', 'close']
        lookback_period: Period for MA and std (e.g., 20)
        num_std: Number of standard deviations (e.g., 2)
    
    Returns:
        pd.DataFrame with columns: ['date', 'close', 'bb_middle', 'bb_upper', 'bb_lower', 'bb_width', 'bb_position']
    """
    import pandas as pd
    import numpy as np
    
    df = stock_df[['date', 'close']].copy()
    df = df.sort_values('date').reset_index(drop=True)
    
    # ✅ VECTORIZED: Bollinger Bands
    df['bb_middle'] = df['close'].rolling(window=lookback_period, min_periods=5).mean()
    df['bb_std'] = df['close'].rolling(window=lookback_period, min_periods=5).std()
    df['bb_upper'] = df['bb_middle'] + (num_std * df['bb_std'])
    df['bb_lower'] = df['bb_middle'] - (num_std * df['bb_std'])
    df['bb_width'] = df['bb_upper'] - df['bb_lower']
    
    # Position within bands (0 = lower, 0.5 = middle, 1 = upper)
    df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower']).replace(0, 1e-10)
    
    return df[['date', 'close', 'bb_middle', 'bb_upper', 'bb_lower', 'bb_width', 'bb_position']]


def calculate_macd_indicator(stock_df, fast_period=12, slow_period=26, signal_period=9):
    """
    Calculate MACD timeseries (VECTORIZED!)
    
    Args:
        stock_df: Stock data with columns ['date', 'close']
        fast_period: Fast EMA period (e.g., 12)
        slow_period: Slow EMA period (e.g., 26)
        signal_period: Signal line period (e.g., 9)
    
    Returns:
        pd.DataFrame with columns: ['date', 'close', 'macd', 'macd_signal', 'macd_hist']
    """
    import pandas as pd
    import numpy as np
    
    df = stock_df[['date', 'close']].copy()
    df = df.sort_values('date').reset_index(drop=True)
    
    # ✅ VECTORIZED: MACD = EMA_fast - EMA_slow
    df['ema_fast'] = df['close'].ewm(span=fast_period, adjust=False).mean()
    df['ema_slow'] = df['close'].ewm(span=slow_period, adjust=False).mean()
    df['macd'] = df['ema_fast'] - df['ema_slow']
    
    # Signal line = EMA of MACD
    df['macd_signal'] = df['macd'].ewm(span=signal_period, adjust=False).mean()
    
    # Histogram = MACD - Signal
    df['macd_hist'] = df['macd'] - df['macd_signal']
    
    return df[['date', 'close', 'macd', 'macd_signal', 'macd_hist']]


def calculate_expected_move_indicator(options_df, stock_df, dte_target=30, dte_tolerance=7):
    """
    Calculate Expected Move from ATM straddle prices (VECTORIZED!)
    
    Args:
        options_df: Options data with columns ['date', 'strike', 'expiration', 'Call/Put', 'bid', 'ask', 'dte']
        stock_df: Stock data with columns ['date', 'close']
        dte_target: Target DTE for options (e.g., 30)
        dte_tolerance: DTE tolerance (e.g., 7)
    
    Returns:
        pd.DataFrame with columns: ['date', 'close', 'atm_straddle_price', 'expected_move', 'expected_move_pct']
    """
    import pandas as pd
    import numpy as np
    
    results = []
    
    # Filter options by DTE range
    dte_min = dte_target - dte_tolerance
    dte_max = dte_target + dte_tolerance
    options_filtered = options_df[(options_df['dte'] >= dte_min) & (options_df['dte'] <= dte_max)].copy()
    
    for date in options_filtered['date'].unique():
        options_today = options_filtered[options_filtered['date'] == date]
        stock_today = stock_df[stock_df['date'] == date]
        
        if len(stock_today) == 0:
            continue
            
        stock_price = stock_today.iloc[0]['close']
        
        # Find ATM strike (closest to stock price)
        strikes = options_today['strike'].unique()
        atm_strike = min(strikes, key=lambda x: abs(x - stock_price))
        
        # Get ATM call and put
        atm_call = options_today[(options_today['strike'] == atm_strike) & (options_today['type'] == 'C')]
        atm_put = options_today[(options_today['strike'] == atm_strike) & (options_today['type'] == 'P')]
        
        if len(atm_call) == 0 or len(atm_put) == 0:
            continue
        
        # Straddle price = (call_bid + call_ask)/2 + (put_bid + put_ask)/2
        call_price = (atm_call.iloc[0]['bid'] + atm_call.iloc[0]['ask']) / 2
        put_price = (atm_put.iloc[0]['bid'] + atm_put.iloc[0]['ask']) / 2
        straddle_price = call_price + put_price
        
        # Expected move (1 std dev move) ≈ straddle price × 0.85
        expected_move = straddle_price * 0.85
        expected_move_pct = (expected_move / stock_price) * 100
        
        results.append({
            'date': date,
            'close': stock_price,
            'atm_straddle_price': straddle_price,
            'expected_move': expected_move,
            'expected_move_pct': expected_move_pct
        })
    
    return pd.DataFrame(results)


def calculate_put_call_ratio_indicator(options_df, dte_target=30, dte_tolerance=7):
    """
    Calculate Put/Call Ratio from option volumes (VECTORIZED!)
    
    Args:
        options_df: Options data with columns ['date', 'Call/Put', 'volume', 'dte']
        dte_target: Target DTE (e.g., 30)
        dte_tolerance: DTE tolerance (e.g., 7)
    
    Returns:
        pd.DataFrame with columns: ['date', 'put_volume', 'call_volume', 'pcr', 'pcr_ma']
    """
    import pandas as pd
    import numpy as np
    
    # Filter by DTE
    dte_min = dte_target - dte_tolerance
    dte_max = dte_target + dte_tolerance
    options_filtered = options_df[(options_df['dte'] >= dte_min) & (options_df['dte'] <= dte_max)].copy()
    
    # Aggregate by date and type
    daily_volumes = options_filtered.groupby(['date', 'Call/Put'])['volume'].sum().unstack(fill_value=0)
    daily_volumes = daily_volumes.reset_index()
    
    if 'C' not in daily_volumes.columns:
        daily_volumes['C'] = 0
    if 'P' not in daily_volumes.columns:
        daily_volumes['P'] = 0
    
    daily_volumes.rename(columns={'C': 'call_volume', 'P': 'put_volume'}, inplace=True)
    
    # ✅ VECTORIZED: P/C Ratio
    daily_volumes['pcr'] = daily_volumes['put_volume'] / daily_volumes['call_volume'].replace(0, 1)
    daily_volumes['pcr_ma'] = daily_volumes['pcr'].rolling(window=10, min_periods=3).mean()
    
    return daily_volumes[['date', 'put_volume', 'call_volume', 'pcr', 'pcr_ma']]


def calculate_hv_iv_ratio_indicator(stock_df, options_df, hv_lookback=30, dte_target=30, dte_tolerance=7):
    """
    Calculate HV/IV Ratio (Historical Vol vs Implied Vol) (VECTORIZED!)
    
    Args:
        stock_df: Stock data with columns ['date', 'close']
        options_df: Options data with columns ['date', 'strike', 'iv', 'dte']
        hv_lookback: Lookback for historical volatility (e.g., 30)
        dte_target: Target DTE for ATM IV (e.g., 30)
        dte_tolerance: DTE tolerance (e.g., 7)
    
    Returns:
        pd.DataFrame with columns: ['date', 'close', 'hv', 'atm_iv', 'hv_iv_ratio']
    """
    import pandas as pd
    import numpy as np
    
    # Calculate Historical Volatility
    df = stock_df[['date', 'close']].copy()
    df = df.sort_values('date').reset_index(drop=True)
    df['returns'] = df['close'].pct_change()
    df['hv'] = df['returns'].rolling(window=hv_lookback, min_periods=10).std() * np.sqrt(252) * 100  # Annualized %
    
    # Get ATM Implied Volatility
    dte_min = dte_target - dte_tolerance
    dte_max = dte_target + dte_tolerance
    options_filtered = options_df[(options_df['dte'] >= dte_min) & (options_df['dte'] <= dte_max)].copy()
    
    atm_iv_by_date = []
    for date in df['date'].unique():
        stock_price = df[df['date'] == date]['close'].values[0] if len(df[df['date'] == date]) > 0 else None
        if stock_price is None:
            continue
        
        options_today = options_filtered[options_filtered['date'] == date]
        if len(options_today) == 0:
            continue
        
        # Find ATM strike
        strikes = options_today['strike'].unique()
        atm_strike = min(strikes, key=lambda x: abs(x - stock_price))
        
        # Get ATM IV (average of call and put)
        atm_options = options_today[options_today['strike'] == atm_strike]
        atm_iv = atm_options['iv'].mean() * 100  # Convert to %
        
        atm_iv_by_date.append({'date': date, 'atm_iv': atm_iv})
    
    iv_df = pd.DataFrame(atm_iv_by_date)
    
    # Merge HV and IV
    result = df.merge(iv_df, on='date', how='left')
    
    # ✅ VECTORIZED: HV/IV Ratio
    result['hv_iv_ratio'] = result['hv'] / result['atm_iv'].replace(0, np.nan)
    
    return result[['date', 'close', 'hv', 'atm_iv', 'hv_iv_ratio']]


class StrategyRegistry:
    """
    Data-driven registry - all logic reads from STRATEGIES dict.
    """
    
    @classmethod
    def get(cls, strategy_type):
        """Get strategy definition from unified STRATEGIES registry"""
        return STRATEGIES.get(strategy_type)
    
    @classmethod
    def is_credit_strategy(cls, strategy_type=None, position=None, entry_price=None, total_cost=None):
        """
        🎯 UNIVERSAL CREDIT/DEBIT DETECTION
        
        Determines if strategy is CREDIT (SHORT) or DEBIT (LONG) dynamically.
        Works for ANY strategy type - no hardcoding needed!
        
        Args:
            strategy_type: Strategy type (optional, for category hint)
            position: Position dict (optional, contains all info)
            entry_price: Entry price (optional, explicit check)
            total_cost: Total cost (optional, explicit check)
        
        Returns:
            bool: True if CREDIT (SHORT), False if DEBIT (LONG)
        
        Detection logic (in priority order):
        1. entry_price == 0 → CREDIT (P&L% mode indicator)
        2. total_cost < 0 → CREDIT (received premium)
        3. is_short_bias flag → CREDIT (explicit indicator)
        4. category == 'CREDIT' → CREDIT (fallback to strategy default)
        5. category == 'NEUTRAL' → False (DEBIT by default for NEUTRAL)
        
        Examples:
            # SHORT Straddle (sell options)
            is_credit_strategy(entry_price=0.0, total_cost=-3000)  # → True
            
            # LONG Straddle (buy options)
            is_credit_strategy(entry_price=3000, total_cost=3000)  # → False
            
            # Iron Condor (always credit)
            is_credit_strategy(strategy_type='IRON_CONDOR')  # → True
        """
        # Extract from position if provided
        if position is not None:
            if entry_price is None:
                entry_price = position.get('entry_price')
            if total_cost is None:
                total_cost = position.get('total_cost')
            if strategy_type is None:
                strategy_type = position.get('strategy_type')
        
        # 1. Check entry_price (most reliable indicator)
        if entry_price is not None and entry_price == 0:
            return True  # P&L% mode = CREDIT
        
        # 2. Check total_cost sign
        if total_cost is not None and total_cost < 0:
            return True  # Negative cost = received premium = CREDIT
        
        # 3. Check explicit is_short_bias flag
        if position is not None:
            is_short = position.get('is_short_bias', None)
            if is_short is not None:
                return is_short
        
        # 4. Fallback to strategy category
        if strategy_type:
            strategy = cls.get(strategy_type)
            if strategy:
                category = strategy.get('category', 'DEBIT')
                return category == 'CREDIT'
        
        # 5. Default: DEBIT (conservative)
        return False
    
    @classmethod
    def calculate_risk(cls, position):
        """
        Calculate capital at risk for any position (data-driven).
        Uses category from STRATEGIES to determine risk calculation.
        """
        position_type = position.get('strategy_type', 'STRADDLE')
        strategy = cls.get(position_type)
        
        if not strategy:
            # Fallback for unknown strategies
            total_cost = abs(position.get('total_cost', 0))
            return total_cost * 2, total_cost
        
        # Extract common variables
        contracts = position.get('contracts', 1)
        total_cost = position.get('total_cost', 0)
        credit = abs(total_cost)
        debit = abs(total_cost)
        premium = abs(total_cost)
        
        # Category-specific calculations (driven by STRATEGIES['category'])
        category = strategy['category']
        
        if category == 'CREDIT':
            # Credit spreads: max loss = (width * 100 * contracts) - credit
            if position_type == 'IRON_CONDOR':
                wing_width = position.get('wing_width', 5)
                max_loss_per_contract = (wing_width * 100) - (credit / contracts if contracts > 0 else 0)
                max_loss = max_loss_per_contract * contracts
                capital_at_risk = max(max_loss * 1.5, credit * 2)
                locked_capital = credit
            
            elif position_type in ['BULL_PUT_SPREAD', 'BEAR_CALL_SPREAD', 'CREDIT_SPREAD']:
                short_strike = position.get('short_strike', 0)
                long_strike = position.get('long_strike', 0)
                if short_strike and long_strike:
                    spread_width = abs(long_strike - short_strike)
                    max_loss = (spread_width * 100 * contracts) - credit
                    capital_at_risk = max(abs(max_loss) * 1.5, credit * 2)
                    locked_capital = credit
                else:
                    capital_at_risk = credit * 2
                    locked_capital = credit
            
            elif position_type == 'IRON_BUTTERFLY':
                wing_width = position.get('wing_width', 10)
                max_loss = (wing_width * 100 * contracts) - credit
                capital_at_risk = max(abs(max_loss) * 1.5, credit * 2)
                locked_capital = credit
            
            else:
                # Generic credit strategy
                capital_at_risk = credit * 2
                locked_capital = credit
        
        elif category == 'DEBIT':
            # Debit strategies: max loss = debit paid
            capital_at_risk = debit * 1.5
            locked_capital = debit
        
        elif category == 'NEUTRAL':
            if position_type == 'COVERED_CALL':
                underlying_price = position.get('underlying_entry_price', 0)
                stock_value = underlying_price * contracts * 100
                # ✅ Use call_premium if available, fallback to credit for backward compatibility
                call_premium = position.get('call_premium', abs(credit))
                capital_at_risk = max(stock_value - call_premium, stock_value * 0.8)
                locked_capital = stock_value
            else:
                # Straddle/Strangle - detect SHORT vs LONG
                # ✅ Universal CREDIT detection
                is_credit = cls.is_credit_strategy(strategy_type=position_type, position=position)
                
                if is_credit:
                    # SHORT: Risk = unlimited (use premium * 2 as conservative estimate)
                    capital_at_risk = premium * 2
                    locked_capital = premium
                else:
                    # LONG: Risk = premium paid (100% loss possible)
                    capital_at_risk = premium * 1.5  # 1.5x buffer for slippage
                    locked_capital = premium
        
        else:
            # Fallback
            capital_at_risk = debit * 2
            locked_capital = debit
        
        return capital_at_risk, locked_capital
    
    @classmethod
    def format_debug_output(cls, strategy_type, entry_context):
        """
        Format debug output for any strategy (data-driven).
        Reads from STRATEGIES['parameters'] dict.
        """
        strategy = cls.get(strategy_type)
        
        if not strategy:
            # Generic fallback
            return [f"  Strategy: {strategy_type}"]
        
        lines = [
            "  ─────────────────────────────────────────",
            f"  Strategy: {strategy['name']}"
        ]
        
        # Iterate over strategy parameters (from unified STRATEGIES!)
        params = strategy.get('parameters', {})
        for param_name, param_meta in params.items():
            if param_name in entry_context and param_meta.get('debug', True):
                value = entry_context[param_name]
                label = param_meta.get('label', param_name)
                format_str = param_meta.get('format', '{}')
                
                try:
                    formatted = format_str.format(value)
                    lines.append(f"  {label}: {formatted}")
                except:
                    lines.append(f"  {label}: {value}")
        
        return lines
    
    @classmethod
    def get_csv_fields(cls, strategy_type):
        """
        Get list of fields to export to CSV (data-driven from STRATEGIES).
        Returns: list of field names where csv=True
        """
        strategy = cls.get(strategy_type)
        if not strategy:
            return []
        
        csv_fields = []
        params = strategy.get('parameters', {})
        for param_name, param_meta in params.items():
            if param_meta.get('csv', True):
                csv_fields.append(param_name)
        
        return csv_fields
    
    @classmethod
    def validate_position(cls, strategy_type, position_data):
        """
        Validate that position has all required fields (data-driven).
        Returns: (is_valid, missing_fields)
        """
        strategy = cls.get(strategy_type)
        if not strategy:
            return True, []
        
        required = strategy.get('required_fields', [])
        missing = [field for field in required if field not in position_data]
        
        return len(missing) == 0, missing
    
    @classmethod
    def get_expected_csv_columns(cls, strategy_type):
        """
        Generate list of expected CSV columns for this strategy (data-driven).
        
        Returns list like:
        ['entry_date', 'exit_date', 'symbol', ..., 'short_call_exit_bid', 'short_call_delta_exit', ...]
        
        This is used for validation and documentation.
        """
        strategy = cls.get(strategy_type)
        
        # Base columns (universal for all strategies)
        columns = [
            'entry_date', 'exit_date', 'symbol', 'signal', 'pnl', 'return_pct', 
            'exit_reason', 'stop_type', 'expiration', 'contracts', 'quantity',
            'entry_price', 'underlying_entry_price', 'iv_rank_entry',
            'stop_threshold', 'actual_value', 'exit_price', 'underlying_exit_price',
            'underlying_change_pct'
        ]
        
        if not strategy or 'legs' not in strategy:
            return columns
        
        # Add leg-specific columns (exit data)
        for leg in strategy['legs']:
            leg_name = leg['name']
            
            # Fields (bid/ask/price)
            for field in leg['fields']:
                columns.append(f"{leg_name}_exit_{field}")
            
            # Greeks (delta, gamma, vega, theta)
            for greek in leg.get('greeks', []):
                columns.append(f"{leg_name}_{greek}_exit")
            
            # IV
            if leg.get('iv', False):
                columns.append(f"{leg_name}_iv_exit")
        
        return columns
    
    @classmethod
    def generate_close_position_kwargs(cls, strategy_type, pos_data):
        """
        Auto-generate kwargs for close_position() based on strategy legs.
        
        Args:
            strategy_type: Strategy type (e.g. 'IRON_CONDOR')
            pos_data: Dict with exit data (e.g. {'short_call_exit_bid': 4.8, ...})
        
        Returns:
            Dict with formatted kwargs for close_position()
            
        Note: This is OPTIONAL - existing code can continue using **pos_data directly.
        This method provides validation and filtering.
        """
        strategy = cls.get(strategy_type)
        
        if not strategy or 'legs' not in strategy:
            # Fallback: filter out fields passed explicitly to close_position()
            excluded = ['pnl', 'pnl_pct', 'price', 'exit_reason', 'close_reason', 'position_id']
            return {k: v for k, v in pos_data.items() if k not in excluded}
        
        kwargs = {}
        
        # Add leg-specific fields
        for leg in strategy['legs']:
            leg_name = leg['name']
            
            # Fields (bid/ask/price)
            for field in leg['fields']:
                key = f"{leg_name}_exit_{field}"
                if key in pos_data:
                    kwargs[key] = pos_data[key]
            
            # Greeks
            for greek in leg.get('greeks', []):
                key = f"{leg_name}_{greek}_exit"
                if key in pos_data:
                    kwargs[key] = pos_data[key]
            
            # IV
            if leg.get('iv', False):
                key = f"{leg_name}_iv_exit"
                if key in pos_data:
                    kwargs[key] = pos_data[key]
        
        # Add other universal fields (underlying_exit_price, directional stop, intraday, etc.)
        universal_fields = [
            # ✅ CRITICAL (v2.16.8): P&L fields (calculated by generate_price_data)
            'pnl_pct', 'pnl', 'price',
            # Underlying fields
            'underlying_exit_price', 'underlying_change_pct', 
            'stop_threshold', 'actual_value',
            # IV Lean specific
            'exit_z_score', 'iv_lean_exit', 'entry_lean', 'exit_lean',
            # Directional stop loss
            'breach_direction', 'stop_level_high', 'stop_level_low',
            # Intraday fields
            'stock_intraday_high', 'stock_intraday_low', 'stock_intraday_close',
            'stock_stop_trigger_time', 'stock_stop_trigger_price',
            'stock_stop_trigger_bid', 'stock_stop_trigger_ask', 'stock_stop_trigger_last',
            'intraday_data_points', 'intraday_data_available', 'stop_triggered_by',
            'intraday_bar_index', 'intraday_volume',
            'intraday_trigger_bid_time', 'intraday_trigger_ask_time'
        ]
        
        for key in universal_fields:
            if key in pos_data:
                kwargs[key] = pos_data[key]
        
        return kwargs
    
    # ========================================================
    # UNIVERSAL CALCULATION METHODS (v2.16.8)
    # ========================================================
    
    @classmethod
    def calculate_close_cost(cls, strategy_type, position, leg_data):
        """
        Calculate cost to CLOSE position (BUY BACK for CREDIT, SELL for DEBIT).
        
        Args:
            strategy_type: Strategy type (e.g. 'IRON_CONDOR', 'STRADDLE')
            position: Position dict with entry data
            leg_data: Dict with CURRENT option prices
                      e.g. {'short_call': sc_eod, 'long_call': lc_eod, ...}
        
        Returns:
            float: Total cost to close position (in $)
            
        Example:
            # Iron Condor (CREDIT - we BUY BACK spreads)
            close_cost = StrategyRegistry.calculate_close_cost(
                'IRON_CONDOR', position,
                {'short_call': sc, 'long_call': lc, 'short_put': sp, 'long_put': lp}
            )
            # Returns: (sc['ask'] - lc['bid'] + sp['ask'] - lp['bid']) * 100 * contracts
        """
        strategy = cls.get(strategy_type)
        if not strategy:
            return 0.0
        
        category = strategy.get('category', 'DEBIT')
        contracts = position.get('contracts', 1)
        
        # Get legs definition
        legs = strategy.get('legs', [])
        if not legs:
            return 0.0
        
        total_cost = 0.0
        
        for leg in legs:
            leg_name = leg['name']
            leg_option = leg_data.get(leg_name)
            
            if leg_option is None:
                continue
            
            # Determine if this leg is SHORT or LONG
            # Convention: leg names with 'short' are sold, others are bought
            is_short_leg = 'short' in leg_name.lower()
            
            # ✅ Universal CREDIT detection (works for ANY strategy)
            is_credit = cls.is_credit_strategy(strategy_type=strategy_type, position=position)
            
            # ⚠️ CRITICAL: For NEUTRAL strategies (STRADDLE, STRANGLE) without 'short' prefix
            # If ALL legs don't have 'short' prefix AND strategy is CREDIT → treat ALL as SHORT
            if is_credit and not is_short_leg and category == 'NEUTRAL':
                # Check if NO legs have 'short' prefix (simple STRADDLE/STRANGLE)
                has_short_prefix = any('short' in l['name'].lower() for l in legs)
                if not has_short_prefix:
                    # Simple STRADDLE/STRANGLE: all legs are SHORT for CREDIT
                    is_short_leg = True
            
            if is_credit:
                # CREDIT strategy: we SOLD initially, now BUY BACK
                # - Short legs: BUY at ASK
                # - Long legs: SELL at BID
                if is_short_leg:
                    leg_cost = leg_option.get('ask', 0) * 100  # Buy at ask
                else:
                    leg_cost = -leg_option.get('bid', 0) * 100  # Sell at bid (negative = we receive)
            else:
                # DEBIT strategy (spreads): we BOUGHT long, SOLD short initially
                # Now to CLOSE: SELL long (receive), BUY BACK short (pay)
                # Net value = long_bid - short_ask
                if is_short_leg:
                    leg_cost = -leg_option.get('ask', 0) * 100   # Buy back short at ask (subtract)
                else:
                    leg_cost = leg_option.get('bid', 0) * 100    # Sell long at bid (add)
            
            total_cost += leg_cost
        
        return total_cost * contracts
    
    @classmethod
    def calculate_entry_cost(cls, strategy_type, leg_data, contracts=1, is_short=None):
        """
        Calculate cost/credit when OPENING position.
        
        Args:
            strategy_type: Strategy type (e.g. 'IRON_CONDOR', 'STRADDLE', 'IV_LEAN')
            leg_data: Dict with option data at entry
            contracts: Number of contracts (default=1 for per-contract calculation)
            is_short: Override for SHORT detection (True = sell to open, False = buy to open)
                     Required for strategies like STRADDLE/IV_LEAN where leg names don't have 'short_' prefix
        
        Returns:
            dict: {
                'total': Total cost (positive for DEBIT, negative for CREDIT),
                'per_leg': {leg_name: cost, ...},  # Individual leg costs
                'net_credit': bool,  # True if net credit received
            }
            
        Example:
            # Iron Condor
            entry_cost = StrategyRegistry.calculate_entry_cost(
                'IRON_CONDOR',
                {'short_call': sc, 'long_call': lc, 'short_put': sp, 'long_put': lp}
            )
            # Returns: {'total': -150, 'per_leg': {...}, 'net_credit': True}
            
            # Short Straddle (IV_LEAN)
            entry_cost = StrategyRegistry.calculate_entry_cost(
                'IV_LEAN',
                {'call': call_data, 'put': put_data},
                contracts=2,
                is_short=True  # ✅ Required for correct BID pricing!
            )
        """
        strategy = cls.get(strategy_type)
        if not strategy:
            return {'total': 0.0, 'per_leg': {}, 'net_credit': False}
        
        category = strategy.get('category', 'DEBIT')
        legs = strategy.get('legs', [])
        
        if not legs:
            return {'total': 0.0, 'per_leg': {}, 'net_credit': False}
        
        per_leg_costs = {}
        total_cost = 0.0
        
        for leg in legs:
            leg_name = leg['name']
            leg_option = leg_data.get(leg_name)
            
            if leg_option is None:
                per_leg_costs[leg_name] = 0.0
                continue
            
            # Determine if this leg is SHORT or LONG
            # 1. If is_short explicitly passed → use it for ALL legs (STRADDLE, IV_LEAN)
            # 2. Otherwise, detect from leg name ('short_call' → SHORT, 'long_call' → LONG)
            # 3. For NEUTRAL strategies without 'short' prefix → auto-detect as SHORT for CREDIT
            if is_short is not None:
                is_short_leg = is_short  # ✅ Override for STRADDLE/IV_LEAN
            else:
                is_short_leg = 'short' in leg_name.lower()
                
                # ✅ AUTO-DETECT: NEUTRAL strategies with no 'short' prefix are typically SHORT
                if not is_short_leg and category == 'NEUTRAL':
                    # Check if NO legs have 'short' prefix (simple STRADDLE/STRANGLE)
                    has_short_prefix = any('short' in l['name'].lower() for l in legs)
                    if not has_short_prefix:
                        # All legs are SHORT (we sell straddle/strangle to open)
                        is_short_leg = True
            
            if category == 'CREDIT':
                # CREDIT strategy: we SELL to open
                # - Short legs: SELL at BID (we receive credit)
                # - Long legs: BUY at ASK (we pay)
                if is_short_leg:
                    leg_cost = -leg_option.get('bid', 0) * 100  # Negative = credit received
                else:
                    leg_cost = leg_option.get('ask', 0) * 100   # Positive = cost paid
            else:
                # DEBIT strategy (spreads): 
                # - Long legs: BUY at ASK (we pay)
                # - Short legs: SELL at BID (we receive credit to offset)
                # Net = Long ASK - Short BID = positive debit
                if is_short_leg:
                    leg_cost = -leg_option.get('bid', 0) * 100  # Negative = credit received
                else:
                    leg_cost = leg_option.get('ask', 0) * 100   # Positive = cost paid
            
            per_leg_costs[leg_name] = leg_cost
            total_cost += leg_cost
        
        total_cost *= contracts
        
        return {
            'total': total_cost,
            'per_leg': per_leg_costs,
            'net_credit': total_cost < 0
        }
    
    @classmethod
    def calculate_entry_risk(cls, strategy_type, entry_cost_info, position_params):
        """
        Calculate MAX RISK for position.
        
        Args:
            strategy_type: Strategy type
            entry_cost_info: Dict from calculate_entry_cost()
            position_params: Dict with strategy-specific params
                            e.g. {'wing_width': 10, 'spread_width': 5, 'contracts': 1}
        
        Returns:
            float: Maximum risk per contract (in $)
            
        Example:
            # Iron Condor: max_risk = (wing_width - credit) * 100
            max_risk = StrategyRegistry.calculate_entry_risk(
                'IRON_CONDOR',
                entry_cost_info={'total': -150, ...},
                position_params={'wing_width': 10, 'contracts': 1}
            )
            # Returns: (10 * 100) - 150 = 850
        """
        strategy = cls.get(strategy_type)
        if not strategy:
            return abs(entry_cost_info.get('total', 0))
        
        category = strategy.get('category', 'DEBIT')
        total_cost = entry_cost_info.get('total', 0)
        contracts = position_params.get('contracts', 1)
        
        # ✅ FIX: NEUTRAL strategies (STRADDLE/STRANGLE) can be DEBIT or CREDIT
        # Check if it's a DEBIT position by looking at total_cost sign
        is_debit = total_cost > 0
        
        if category == 'DEBIT' or (category == 'NEUTRAL' and is_debit):
            # DEBIT: max risk = premium paid (total_cost already includes contracts)
            return abs(total_cost)
        
        # CREDIT: max risk depends on strategy
        # NOTE: total_cost is ALREADY multiplied by contracts in calculate_entry_cost()!
        if strategy_type == 'IRON_CONDOR':
            wing_width = position_params.get('wing_width', 0)
            # Max risk = (wing_width * 100 * contracts) - credit (only ONE side can lose)
            # total_cost is negative for credit, so we add it
            return (wing_width * 100 * contracts) + total_cost  # ✅ FIXED: total_cost already includes contracts
        
        elif strategy_type in ['BULL_PUT_SPREAD', 'BEAR_CALL_SPREAD', 'CREDIT_SPREAD']:
            spread_width = position_params.get('spread_width', 0)
            # Max risk = (spread_width * 100 * contracts) - credit
            return (spread_width * 100 * contracts) + total_cost  # ✅ FIXED: total_cost already includes contracts
        
        elif strategy_type == 'IRON_BUTTERFLY':
            wing_width = position_params.get('wing_width', 0)
            # Max risk = (wing_width * 100 * contracts) - credit (similar to Iron Condor)
            return (wing_width * 100 * contracts) + total_cost  # ✅ FIXED: total_cost already includes contracts
        
        elif strategy_type == 'COVERED_CALL':
            # Max risk = stock cost - call premium (stock can go to $0, but we keep premium)
            stock_price = position_params.get('stock_price', 0)
            # total_cost is negative (credit from selling call), so adding it reduces risk
            return (stock_price * 100 * contracts) + total_cost  # ✅ FIXED: subtract call premium
        
        elif strategy_type == 'CASH_SECURED_PUT':
            strike = position_params.get('strike', 0)
            # Max risk = (strike * contracts) - premium (if stock goes to $0)
            return (strike * 100 * contracts) + total_cost  # ✅ FIXED: total_cost already includes contracts
        
        elif strategy_type in ['IV_LEAN', 'STRADDLE', 'STRANGLE'] or category == 'NEUTRAL':
            # ✅ FIX: For short NEUTRAL strategies (short straddle/strangle in IV_LEAN)
            # max_risk = premium received (same as debit - we track it as capital at risk)
            # This matches how PositionManager calculates entry_max_risk for these strategies
            return abs(total_cost)
        
        else:
            # Default: assume max risk is 2x credit (conservative)
            return abs(total_cost) * 2
    
    @classmethod
    def prepare_entry_context(cls, strategy_type=None, entry_cost_info=None, max_risk=None, 
                             leg_data=None, config=None, current_date=None):
        """
        Prepare entry_context dict for position sizing and debug output.
        
        Auto-extracts parameters from config and STRATEGIES registry for data-driven approach.
        
        Args:
            strategy_type: Strategy type (optional if config is provided)
            entry_cost_info: Dict from calculate_entry_cost()
            max_risk: Max risk from calculate_entry_risk()
            leg_data: Dict with option data
            config: Optional config dict (for auto-extraction of strategy params & indicators)
                   If provided and contains 'strategy_type', it overrides strategy_type parameter
            current_date: Optional current date (for extracting indicators from indicator_lookup)
        
        Returns:
            dict: Context dict with strategy-specific fields
            
        Example (OLD - manual):
            entry_context = StrategyRegistry.prepare_entry_context(
                strategy_type='IRON_CONDOR',
                entry_cost_info=entry_cost_info,
                max_risk=max_risk,
                leg_data=leg_data
            )
            
        Example (NEW - automatic, NO duplication):
            entry_context = StrategyRegistry.prepare_entry_context(
                entry_cost_info=entry_cost_info,
                max_risk=max_risk,
                leg_data=leg_data,
                config=config,              # ← strategy_type читается отсюда!
                current_date=current_date
            )
            # ✅ All params auto-extracted from config + STRATEGIES dict:
            # - strategy_type (from config['strategy_type'])
            # - wing_width, call_delta, put_delta (from config)
            # - iv_rank, iv_skew (from indicator_lookup)
            # - deltas, IVs (from leg_data)
        """
        # ✅ Auto-read strategy_type from config if provided (eliminates duplication!)
        if config and 'strategy_type' in config:
            strategy_type = config['strategy_type']
        
        if not strategy_type:
            return {}
        
        strategy = cls.get(strategy_type)
        if not strategy:
            return {}
        
        context = {'strategy_type': strategy_type}
        
        # ✅ Universal CREDIT detection (based on entry_cost_info sign)
        if entry_cost_info:
            is_credit = entry_cost_info.get('total', 0) < 0
            
            # Universal fields
            if is_credit:
                context['total_credit'] = abs(entry_cost_info['total'])
                if max_risk is not None:
                    context['max_risk'] = max_risk
                
                # Add per-leg credits if available
                per_leg = entry_cost_info.get('per_leg', {})
                for leg_name, cost in per_leg.items():
                    if 'short' in leg_name:
                        context[f"{leg_name}_credit"] = abs(cost)
            else:
                context['total_premium'] = abs(entry_cost_info.get('total', 0))
                if max_risk is not None:
                    context['max_risk'] = max_risk
        
        # Extract deltas from leg_data
        if leg_data:
            for leg_name, leg_option in leg_data.items():
                if leg_option is not None and hasattr(leg_option, 'get'):
                    delta = leg_option.get('delta')
                    if delta is not None:
                        context[f"{leg_name}_delta"] = delta
                    
                    # Also add IV if available
                    iv = leg_option.get('iv')
                    if iv is not None:
                        context[f"{leg_name}_iv"] = iv
        
        # ✅ NEW: Auto-extract strategy parameters from config (data-driven!)
        if config:
            params = strategy.get('parameters', {})
            
            for param_name in params.keys():
                # Try direct match first (e.g., 'wing_width')
                if param_name in config:
                    context[param_name] = config[param_name]
                # Try with '_target' suffix (e.g., 'call_delta_target' → 'call_delta')
                elif f"{param_name}_target" in config:
                    context[param_name] = config[f"{param_name}_target"]
            
            # ✅ NEW: Auto-extract indicators from indicator_lookup
            if current_date:
                indicator_lookup = config.get('indicator_lookup', {})
                if indicator_lookup and current_date in indicator_lookup:
                    indicators = indicator_lookup[current_date]
                    
                    # Add all indicators to context (e.g., iv_rank, iv_skew)
                    for ind_name, ind_value in indicators.items():
                        if ind_value is not None:
                            context[ind_name] = ind_value
        
        return context
    
    @classmethod
    def generate_price_data(cls, strategy_type, leg_data, underlying_price, 
                           position=None, pnl=None, underlying_change_pct=None, pnl_pct=None,
                           context='stop_loss'):
        """
        Auto-generate price_data dict for check_positions() based on strategy legs.
        
        ✨ NEW in v2.16.8: If 'position' is provided, automatically calculates P&L!
        
        Args:
            strategy_type: Strategy type (e.g. 'STRADDLE', 'IRON_CONDOR')
            leg_data: Dict with CURRENT option prices
                      e.g. {'call': call_eod, 'put': put_eod}
                      or {'short_call': sc_eod, 'long_call': lc_eod, ...}
            underlying_price: Current underlying price
            position: (OPTIONAL) Position dict - if provided, will auto-calculate P&L
            pnl: (OPTIONAL) Current P&L ($) - only needed if position not provided
            underlying_change_pct: (OPTIONAL) Underlying change % - auto-calculated if position provided
            pnl_pct: (OPTIONAL) Current P&L (%) - auto-calculated if position provided
        
        Returns:
            Dict with complete price_data for check_positions()
            
        Example (NEW - automatic):
            # ✅ RECOMMENDED: Let framework calculate P&L
            price_data = StrategyRegistry.generate_price_data(
                strategy_type='IRON_CONDOR',
                leg_data={'short_call': sc_eod, 'long_call': lc_eod, ...},
                underlying_price=stock_price,
                position=position  # Framework calculates P&L automatically!
            )
            
        Example (OLD - manual, still supported):
            # ⚠️ LEGACY: Manual P&L calculation
            price_data = StrategyRegistry.generate_price_data(
                strategy_type='STRADDLE',
                leg_data={'call': call_eod, 'put': put_eod},
                underlying_price=stock_price,
                pnl=current_pnl,
                underlying_change_pct=underlying_change_pct,
                pnl_pct=pnl_pct
            )
        """
        strategy = cls.get(strategy_type)
        category = strategy.get('category', 'DEBIT') if strategy else 'DEBIT'
        
        # ========================================================
        # AUTOMATIC P&L CALCULATION (if position provided)
        # ========================================================
        if position is not None:
            # 1. Calculate close cost
            close_cost = cls.calculate_close_cost(strategy_type, position, leg_data)
            
            # 2. Calculate P&L
            entry_cost = position.get('total_cost', 0)
            
            # ✅ Universal CREDIT detection (works for ANY strategy)
            is_credit = cls.is_credit_strategy(strategy_type=strategy_type, position=position)
            
            if is_credit:
                # CREDIT: pnl = credit_received - buyback_cost
                # ✅ entry_cost is stored as NEGATIVE for credits, use abs()
                # close_cost is cost to buy back
                pnl = abs(entry_cost) - close_cost
            else:
                # DEBIT: pnl = sell_price - buy_price
                # entry_cost is stored as POSITIVE (premium paid)
                # close_cost is what we receive when selling
                pnl = close_cost - entry_cost
            
            # 3. Calculate P&L% (CORRECTLY for CREDIT vs DEBIT!)
            if is_credit:
                # ✅ CREDIT: % based on context
                # context='profit_target' → % from CREDIT (max profit)
                # context='stop_loss'     → % from MAX_RISK
                max_risk_total = position.get('entry_max_risk', 0)
                credit_received = abs(entry_cost)
                
                if context == 'profit_target':
                    # 🎯 PROFIT TARGET: % from max profit (credit received)
                    # Example: Got $1000 credit, made $500 profit → 50% of max profit
                    if credit_received > 0:
                        pnl_pct = (pnl / credit_received) * 100
                        print(f"[DEBUG P&L%] PROFIT_TARGET mode: pnl=${pnl:.2f} / credit=${credit_received:.2f} = {pnl_pct:.2f}%")
                    else:
                        pnl_pct = 0
                else:
                    # 🛑 STOP-LOSS: % from max risk
                    # Example: Risk $10k, lost $2k → -20% of max risk
                    if max_risk_total > 0:
                        pnl_pct = (pnl / max_risk_total) * 100
                    else:
                        # Fallback: use credit as denominator
                        pnl_pct = (pnl / credit_received) * 100 if credit_received != 0 else 0
            else:
                # ✅ DEBIT: % based on premium paid
                pnl_pct = (pnl / entry_cost) * 100 if entry_cost > 0 else 0
            
            # 4. Calculate underlying change %
            entry_underlying = position.get('underlying_entry_price', 0)
            if entry_underlying > 0:
                underlying_change_pct = ((underlying_price - entry_underlying) / entry_underlying) * 100
            else:
                underlying_change_pct = 0.0
        
        # ========================================================
        # FALLBACK: Manual P&L (for backward compatibility)
        # ========================================================
        else:
            # Legacy mode: use provided values
            if pnl is None:
                pnl = 0.0
            if pnl_pct is None:
                pnl_pct = pnl  # Fallback
            if underlying_change_pct is None:
                underlying_change_pct = 0.0
        
        # Base fields (universal)
        price_data = {
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'price': pnl_pct,  # For compatibility
            'underlying_price': underlying_price,
            'underlying_exit_price': underlying_price,  # Legacy alias for underlying_price
            'underlying_change_pct': underlying_change_pct
        }
        
        if not strategy or 'legs' not in strategy:
            # Fallback: no leg-specific fields
            return price_data
        
        # Helper to safely get greek
        def safe_get_greek(data, greek_name):
            if data is None:
                return None
            
            # Try 1: Check if greek is directly in data (e.g., from pandas Series.to_dict())
            if greek_name in data:
                return data[greek_name]
            
            # Try 2: Check if greeks are nested in data['greeks'] (legacy structure)
            greeks = data.get('greeks', {})
            if isinstance(greeks, dict) and greek_name in greeks:
                return greeks[greek_name]
            
            return None
        
        # Add leg-specific fields
        for leg in strategy['legs']:
            leg_name = leg['name']
            
            # Get raw data for this leg
            if leg_name not in leg_data:
                continue
            
            raw_data = leg_data[leg_name]
            if raw_data is None:
                continue
            
            # Fields (bid/ask/price)
            for field in leg['fields']:
                key = f"{leg_name}_exit_{field}"
                if field in raw_data:
                    price_data[key] = raw_data[field]
            
            # Greeks
            for greek in leg.get('greeks', []):
                key = f"{leg_name}_{greek}_exit"
                value = safe_get_greek(raw_data, greek)
                if value is not None:
                    price_data[key] = value
            
            # IV
            if leg.get('iv', False):
                key = f"{leg_name}_iv_exit"
                if 'iv' in raw_data:
                    price_data[key] = raw_data['iv']
        
        # Auto-calculate derived fields for specific strategies
        if strategy_type in ['STRADDLE', 'STRANGLE', 'IV_LEAN']:
            # Calculate IV lean if we have call and put IV
            call_iv = leg_data.get('call', {}).get('iv') if 'call' in leg_data else None
            put_iv = leg_data.get('put', {}).get('iv') if 'put' in leg_data else None
            if call_iv is not None and put_iv is not None:
                price_data['iv_lean_exit'] = call_iv - put_iv
        
        return price_data
    
    @classmethod
    def generate_close_position_kwargs(cls, strategy_type, pos_data):
        """
        Auto-generate kwargs for close_position() based on strategy's legs structure.
        
        Args:
            strategy_type (str): Strategy type ('STRADDLE', 'IRON_CONDOR', etc.)
            pos_data (dict): Position data containing leg-specific exit fields (from generate_price_data())
        
        Returns:
            dict: Filtered kwargs for close_position() containing only leg-specific + universal fields
        
        Example:
            pos_data = {
                'pnl': 150.0,
                'underlying_price': 100.5,
                'call_exit_bid': 5.2,
                'call_delta_exit': 0.5,
                'call_gamma_exit': 0.02,
                ...
            }
            kwargs = StrategyRegistry.generate_close_position_kwargs('STRADDLE', pos_data)
            # Returns: {
            #     'underlying_exit_price': 100.5,
            #     'underlying_change_pct': ...,
            #     'call_exit_bid': 5.2,
            #     'call_exit_ask': 5.4,
            #     'call_delta_exit': 0.5,
            #     'call_gamma_exit': 0.02,
            #     'call_vega_exit': 15.5,
            #     'call_theta_exit': -3.2,
            #     'call_iv_exit': 0.35,
            #     'put_exit_bid': 4.8,
            #     'put_exit_ask': 5.0,
            #     ...
            # }
        """
        strategy = cls.get(strategy_type)
        if not strategy or 'legs' not in strategy:
            # Fallback: return all pos_data (for backward compatibility)
            # BUT exclude fields that are ALWAYS passed explicitly to close_position()
            excluded_fields = ['pnl', 'pnl_pct', 'price', 'exit_reason', 'close_reason', 'position_id']
            kwargs = {k: v for k, v in pos_data.items() if k not in excluded_fields}
            return kwargs
        
        kwargs = {}
        
        # 1. Add universal fields (always included)
        universal_fields = [
            'underlying_exit_price', 'underlying_change_pct',
            'exit_z_score', 'iv_lean_exit', 'iv_rank_exit',
            # Stop-loss fields (passed from stop_info, not from price_data)
            'stop_threshold', 'actual_value',
            # IV Lean strategy-specific fields (market lean from calculate_iv_lean_zscore)
            # NOTE: These are DIFFERENT from iv_lean_entry/exit (position lean)
            'entry_lean', 'exit_lean',
            # Intraday fields
            'stock_stop_trigger_time', 'stock_stop_trigger_price',
            'stock_stop_trigger_bid', 'stock_stop_trigger_ask',
            'intraday_data_points', 'intraday_data_available',
            'stop_triggered_by', 'breach_direction',
            'stop_level_high', 'stop_level_low',
            'intraday_bar_index', 'intraday_volume',
            'stock_stop_trigger_bid_time', 'stock_stop_trigger_ask_time',
        ]
        for field in universal_fields:
            if field in pos_data:
                kwargs[field] = pos_data[field]
        
        # 2. Add leg-specific exit fields (based on strategy's legs structure)
        for leg in strategy['legs']:
            leg_name = leg['name']
            
            # Fields (bid/ask/price)
            for field in leg['fields']:
                key = f"{leg_name}_exit_{field}"
                if key in pos_data:
                    kwargs[key] = pos_data[key]
            
            # Greeks
            for greek in leg.get('greeks', []):
                key = f"{leg_name}_{greek}_exit"
                if key in pos_data:
                    kwargs[key] = pos_data[key]
            
            # IV
            if leg.get('iv', False):
                key = f"{leg_name}_iv_exit"
                if key in pos_data:
                    kwargs[key] = pos_data[key]
        
        return kwargs
    
    @classmethod
    def get_leg_data_for_position(cls, position, options_df, get_option_func):
        """
        Universal function to get leg data for any strategy type.
        
        Args:
            position (dict): Position dict with strategy_type, strikes, expiration
            options_df (DataFrame): DataFrame with filtered options (options_today)
            get_option_func (callable): Function to get option data by (strike, exp, type)
                                       e.g., get_option_by_strike_exp
        
        Returns:
            dict: {'short_call': option_data, 'long_call': option_data, ...}
            None: If any leg data is missing
            
        Example:
            leg_data = StrategyRegistry.get_leg_data_for_position(
                position, 
                options_today, 
                lambda s, e, t: get_option_by_strike_exp(options_today, s, e, t)
            )
        """
        strategy_type = position.get('strategy_type', 'UNKNOWN')
        expiration = position.get('expiration')
        
        # Get strategy info from registry
        strategy = cls.get(strategy_type)
        if not strategy:
            return None
        
        legs = strategy.get('legs', [])
        leg_data = {}
        
        # Fetch data for each leg
        for leg in legs:
            leg_name = leg['name']
            strike_key = f"{leg_name}_strike"
            strike = position.get(strike_key)
            
            # Fallback: for STRADDLE/IV_LEAN where call and put have SAME strike
            if strike is None:
                strike = position.get('strike')
            
            if strike is None:
                return None  # Missing strike data
            
            # Determine option type from leg name
            if 'call' in leg_name.lower():
                opt_type = 'C'
            elif 'put' in leg_name.lower():
                opt_type = 'P'
            else:
                return None  # Unknown leg type
            
            # Fetch option data
            option_data = get_option_func(strike, expiration, opt_type)
            if option_data is None:
                return None  # Missing option data
            
            leg_data[leg_name] = option_data
        
        return leg_data if leg_data else None

def create_optimization_folder(base_dir='optimization_results'):
    """
    Create timestamped folder for optimization run
    Returns: folder path (e.g., 'optimization_results/20250122_143025')
    """
    from pathlib import Path
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    folder_path = Path(base_dir) / timestamp
    folder_path.mkdir(parents=True, exist_ok=True)
    print(f"\n📁 Created optimization folder: {folder_path}")
    return str(folder_path)

# ============================================================
# RESOURCE MONITOR
# ============================================================
class ResourceMonitor:
    """Monitor CPU and RAM with container support"""
    
    def __init__(self, show_container_total=False):
        self.process = psutil.Process()
        self.cpu_count = psutil.cpu_count()
        self.last_cpu_time = None
        self.last_check_time = None
        self.use_cgroups = self._check_cgroups_v2()
        self.show_container_total = show_container_total
        self.cpu_history = []
        self.cpu_history_max = 5
        
        if self.use_cgroups:
            quota = self._read_cpu_quota()
            if quota and quota > 0:
                self.cpu_count = quota
        
        self.context = "Container" if self.use_cgroups else "Host"
        
    def _read_cpu_quota(self):
        try:
            with open('/sys/fs/cgroup/cpu.max', 'r') as f:
                line = f.read().strip()
                if line == 'max':
                    return None
                parts = line.split()
                if len(parts) == 2:
                    quota = int(parts[0])
                    period = int(parts[1])
                    return quota / period
        except:
            pass
        return None
        
    def get_context_info(self):
        if self.use_cgroups:
            current, max_mem = self._read_cgroup_memory()
            ram_info = ""
            if max_mem:
                max_mem_gb = max_mem / (1024**3)
                ram_info = f", {max_mem_gb:.1f}GB limit"
            
            mem_type = "container total" if self.show_container_total else "process only"
            return f"Container (CPU: {self.cpu_count:.1f} cores{ram_info}) - RAM: {mem_type}"
        else:
            total_ram_gb = psutil.virtual_memory().total / (1024**3)
            return f"Host ({self.cpu_count} cores, {total_ram_gb:.0f}GB RAM) - RAM: process"
        
    def _check_cgroups_v2(self):
        try:
            return os.path.exists('/sys/fs/cgroup/cpu.stat') and \
                   os.path.exists('/sys/fs/cgroup/memory.current')
        except:
            return False
    
    def _read_cgroup_cpu(self):
        try:
            with open('/sys/fs/cgroup/cpu.stat', 'r') as f:
                for line in f:
                    if line.startswith('usage_usec'):
                        return int(line.split()[1])
        except:
            pass
        return None
    
    def _read_cgroup_memory(self):
        try:
            with open('/sys/fs/cgroup/memory.current', 'r') as f:
                current = int(f.read().strip())
            with open('/sys/fs/cgroup/memory.max', 'r') as f:
                max_mem = f.read().strip()
                if max_mem == 'max':
                    max_mem = psutil.virtual_memory().total
                else:
                    max_mem = int(max_mem)
            return current, max_mem
        except:
            pass
        return None, None
    
    def get_cpu_percent(self):
        if self.use_cgroups:
            current_time = time.time()
            current_cpu = self._read_cgroup_cpu()
            
            if current_cpu and self.last_cpu_time and self.last_check_time:
                time_delta = current_time - self.last_check_time
                cpu_delta = current_cpu - self.last_cpu_time
                
                if time_delta > 0:
                    cpu_percent = (cpu_delta / (time_delta * 1_000_000)) * 100
                    cpu_percent = min(cpu_percent, 100 * self.cpu_count)
                    
                    self.cpu_history.append(cpu_percent)
                    if len(self.cpu_history) > self.cpu_history_max:
                        self.cpu_history.pop(0)
                    
                    self.last_cpu_time = current_cpu
                    self.last_check_time = current_time
                    
                    return round(sum(self.cpu_history) / len(self.cpu_history), 1)
            
            self.last_cpu_time = current_cpu
            self.last_check_time = current_time
        
        try:
            cpu = self.process.cpu_percent(interval=0.1)
            if cpu == 0:
                cpu = psutil.cpu_percent(interval=0.1)
            
            self.cpu_history.append(cpu)
            if len(self.cpu_history) > self.cpu_history_max:
                self.cpu_history.pop(0)
            
            return round(sum(self.cpu_history) / len(self.cpu_history), 1)
        except:
            return 0.0
    
    def get_memory_info(self):
        try:
            mem = self.process.memory_info()
            process_mb = mem.rss / (1024 * 1024)
            
            if self.use_cgroups:
                current, max_mem = self._read_cgroup_memory()
                if max_mem:
                    process_percent = (mem.rss / max_mem) * 100
                    
                    if current:
                        container_mb = current / (1024 * 1024)
                        container_percent = (current / max_mem) * 100
                        return (
                            round(process_mb, 1), 
                            round(process_percent, 1),
                            round(container_mb, 1),
                            round(container_percent, 1)
                        )
                    
                    return (
                        round(process_mb, 1), 
                        round(process_percent, 1),
                        round(process_mb, 1),
                        round(process_percent, 1)
                    )
            
            total = psutil.virtual_memory().total
            percent = (mem.rss / total) * 100
            
            return (
                round(process_mb, 1), 
                round(percent, 1),
                round(process_mb, 1),
                round(percent, 1)
            )
            
        except:
            return 0.0, 0.0, 0.0, 0.0


def create_progress_bar(reuse_existing=None):
    """Create or reuse enhanced progress bar"""
    if reuse_existing is not None:
        progress_bar, status_label, monitor, start_time = reuse_existing
        progress_bar.value = 0
        progress_bar.bar_style = 'info'
        status_label.value = "<b style='color:#0066cc'>Starting...</b>"
        return progress_bar, status_label, monitor, time.time()
    
    try:
        from IPython.display import display
        import ipywidgets as widgets
        
        progress_bar = widgets.FloatProgress(
            value=0, min=0, max=100,
            description='Progress:',
            bar_style='info',
            style={'bar_color': '#00ff00'},
            layout=widgets.Layout(width='100%', height='30px')
        )
        
        status_label = widgets.HTML(
            value="<b style='color:#0066cc'>Starting...</b>"
        )
        
        display(widgets.VBox([progress_bar, status_label]))
        
        monitor = ResourceMonitor()
        start_time = time.time()
        
        return progress_bar, status_label, monitor, start_time
    except ImportError:
        print("Warning: ipywidgets not available. Progress bar disabled.")
        return None, None, ResourceMonitor(), time.time()


def update_progress(progress_bar, status_label, monitor, current, total, start_time, message="Processing"):
    """Update progress bar with ETA, CPU%, RAM"""
    if progress_bar is None or status_label is None:
        return
    
    progress = (current / total) * 100
    progress_bar.value = progress
    
    elapsed = time.time() - start_time
    if current > 0:
        eta_seconds = (elapsed / current) * (total - current)
        eta_str = format_time(eta_seconds)
    else:
        eta_str = "calculating..."
    
    cpu = monitor.get_cpu_percent()
    process_mb, process_pct, container_mb, container_pct = monitor.get_memory_info()
    
    if abs(container_mb - process_mb) > 10:
        ram_display = (
            f"RAM: <span style='color:#4CAF50'>{process_mb}MB ({process_pct}%)</span> Python | "
            f"<span style='color:#2196F3'>{container_mb}MB ({container_pct}%)</span> Container"
        )
    else:
        ram_display = f"RAM: {process_mb}MB ({process_pct}%)"
    
    context_info = monitor.get_context_info()

    elapsed_str = format_time(elapsed)
    start_time_str = datetime.fromtimestamp(start_time).strftime('%H:%M:%S')
    
    status_label.value = (
        f"<b style='color:#0066cc'>{message} ({current}/{total})</b><br>"
        f"<span style='color:#666'>⏱️ Elapsed: {elapsed_str} | ETA: {eta_str} | Started: {start_time_str}</span><br>"
        f"<span style='color:#666'>CPU: {cpu}% | {ram_display}</span><br>"
        f"<span style='color:#999;font-size:10px'>{context_info}</span>"
    )


def format_time(seconds):
    """Format seconds to human readable time"""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        return f"{int(seconds // 60)}m {int(seconds % 60)}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


# ============================================================
# API HELPER
# ============================================================
class APIHelper:
    """Normalizes API responses"""
    
    @staticmethod
    def normalize_response(response, debug=False):
        if response is None:
            if debug:
                print("[APIHelper] Response is None")
            return None
        
        if isinstance(response, dict):
            if 'data' in response:
                if debug:
                    print(f"[APIHelper] Dict response: {len(response['data'])} records")
                return response
            else:
                if debug:
                    print("[APIHelper] Dict without 'data' key")
                return None
        
        if isinstance(response, pd.DataFrame):
            if response.empty:
                if debug:
                    print("[APIHelper] Empty DataFrame")
                return None
            
            records = response.to_dict('records')
            if debug:
                print(f"[APIHelper] DataFrame converted: {len(records)} records")
            return {'data': records, 'status': 'success'}
        
        if debug:
            print(f"[APIHelper] Unexpected type: {type(response)}")
        return None


class APIManager:
    """Centralized API key management"""
    _api_key = None
    _methods = {}
    
    @classmethod
    def initialize(cls, api_key):
        if not api_key:
            raise ValueError("API key cannot be empty")
        cls._api_key = api_key
        ivol.setLoginParams(apiKey=api_key)
        print(f"[API] Initialized: {api_key[:10]}...{api_key[-5:]}")
    
    @classmethod
    def get_method(cls, endpoint):
        if cls._api_key is None:
            api_key = os.getenv("API_KEY")
            if not api_key:
                raise ValueError("API key not set. Call init_api(key) first")
            cls.initialize(api_key)
        
        if endpoint not in cls._methods:
            ivol.setLoginParams(apiKey=cls._api_key)
            cls._methods[endpoint] = ivol.setMethod(endpoint)
        
        return cls._methods[endpoint]


def init_api(api_key):
    """Initialize IVolatility API"""
    APIManager.initialize(api_key)


def api_call(endpoint, cache_config=None, debug=False, max_retries=3, **kwargs):
    """
    Make API call with automatic response normalization, caching, and retry logic
    
    Args:
        endpoint: API endpoint path
        cache_config: Cache configuration dict (optional, enables caching if provided)
        debug: Debug mode flag (bool or int for debug level)
        max_retries: Maximum number of retry attempts for network errors (default: 3)
        **kwargs: API parameters
    
    Returns:
        Normalized API response or None
    """
    import time
    from http.client import RemoteDisconnected
    from requests.exceptions import ConnectionError, Timeout, RequestException
    
    # Support both bool and int debug levels
    debug_level = 3 if (isinstance(debug, int) and debug >= 3) else (1 if debug else 0)
    
    # Network errors that should trigger retry
    RETRYABLE_ERRORS = (
        RemoteDisconnected,
        ConnectionError,
        Timeout,
        RequestException,
    )
    
    last_exception = None
    
    # Retry loop with exponential backoff
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                # Exponential backoff: 2s, 4s, 8s...
                wait_time = 2 ** attempt
                if debug_level >= 1:
                    print(f"[RETRY] Attempt {attempt + 1}/{max_retries} after {wait_time}s delay...")
                time.sleep(wait_time)
            
            return _api_call_internal(endpoint, cache_config, debug, debug_level, **kwargs)
        
        except RETRYABLE_ERRORS as e:
            last_exception = e
            if debug_level >= 1:
                print(f"[RETRY] Network error on attempt {attempt + 1}/{max_retries}: {type(e).__name__}: {e}")
            
            # If this was the last attempt, re-raise
            if attempt == max_retries - 1:
                if debug_level >= 1:
                    print(f"[RETRY] ❌ All {max_retries} attempts failed. Giving up.")
                raise
            
            # Otherwise continue to next retry
            continue
        
        except Exception as e:
            # Non-retryable error - fail immediately
            if debug:
                print(f"[api_call] Non-retryable exception: {e}")
                print(f"[api_call] Endpoint: {endpoint}")
                print(f"[api_call] Params: {kwargs}")
            return None
    
    # Should never reach here, but just in case
    return None


def _api_call_internal(endpoint, cache_config, debug, debug_level, **kwargs):
    """
    Internal API call implementation (wrapped by retry logic)
    """
    import time
    
    try:
        
        # TIMING: Start total timer
        t_start_total = time.perf_counter()
        
        if debug_level >= 3:
            print(f"\n{'='*80}")
            print(f"[API DEBUG] Starting API call to: {endpoint}")
            print(f"[API DEBUG] Parameters: {kwargs}")
            print(f"{'='*80}")
        
        # Check if caching is enabled
        use_cache = cache_config is not None and (
            cache_config.get('disk_enabled', False) or 
            cache_config.get('memory_enabled', False)
        )
        
        cache_manager = None
        cache_key = None
        data_type = None
        
        if use_cache:
            # TIMING: Cache key generation
            t_cache_key_start = time.perf_counter()
            
            # Initialize cache manager
            cache_manager = UniversalCacheManager(cache_config)
            
            # Create cache key from endpoint and params (human-readable)
            # Determine data type based on endpoint (supports EOD + INTRADAY for both STOCK + OPTIONS)
            is_intraday = 'intraday' in endpoint
            is_options = 'options' in endpoint
            is_stock = 'stock' in endpoint
            
            if is_intraday and is_options:
                # Intraday options data: /equities/intraday/options-rawiv
                data_type = 'options_intraday'
                symbol = kwargs.get('symbol', 'UNKNOWN')
                date = kwargs.get('date', 'UNKNOWN')
                cache_key = f"{symbol}_{date}"
            elif is_intraday and is_stock:
                # Intraday stock data: /equities/intraday/stock-prices
                data_type = 'stock_intraday'
                symbol = kwargs.get('symbol', 'UNKNOWN')
                date = kwargs.get('date', 'UNKNOWN')
                cache_key = f"{symbol}_{date}"
            elif 'stock-opts-by-param' in endpoint:
                # EOD options by param: /equities/eod/stock-opts-by-param
                data_type = 'options_by_param'
                symbol = kwargs.get('symbol', 'UNKNOWN')
                # Support both tradeDate (single day) and startDate/endDate (range)
                start_date = kwargs.get('startDate', kwargs.get('tradeDate', 'UNKNOWN'))
                end_date = kwargs.get('endDate', start_date)
                cp = kwargs.get('cp', 'X')
                dte_from = kwargs.get('dteFrom', 0)
                dte_to = kwargs.get('dteTo', 999)
                if start_date == end_date:
                    cache_key = f"{symbol}_{start_date}_{cp}_dte{dte_from}-{dte_to}"
                else:
                    cache_key = f"{symbol}_{start_date}_{end_date}_{cp}_dte{dte_from}-{dte_to}"
            elif is_options:
                # EOD options data: /equities/eod/options-rawiv
                data_type = 'options_eod'
                symbol = kwargs.get('symbol', 'UNKNOWN')
                from_date = kwargs.get('from_', kwargs.get('date', 'UNKNOWN'))
                to_date = kwargs.get('to', from_date)
                if from_date != to_date:
                    cache_key = f"{symbol}_{from_date}_{to_date}"
                else:
                    cache_key = f"{symbol}_{from_date}"
            elif is_stock:
                # EOD stock data: /equities/eod/stock-prices
                data_type = 'stock_eod'
                symbol = kwargs.get('symbol', 'UNKNOWN')
                from_date = kwargs.get('from_', kwargs.get('date', 'UNKNOWN'))
                to_date = kwargs.get('to', from_date)
                if from_date != to_date:
                    cache_key = f"{symbol}_{from_date}_{to_date}"
                else:
                    cache_key = f"{symbol}_{from_date}"
            else:
                # Fallback for other endpoints
                sorted_params = sorted([(k, v) for k, v in kwargs.items()])
                param_hash = abs(hash(str(sorted_params)))
                cache_key = f"{endpoint.replace('/', '_')}_{param_hash}"
                data_type = 'default'
            
            t_cache_key_elapsed = (time.perf_counter() - t_cache_key_start) * 1000  # ms
            
            if debug_level >= 3:
                print(f"[STEP 1] Cache key generation: {t_cache_key_elapsed:.2f}ms")
                print(f"         Cache key: {cache_key}")
                print(f"         Data type: {data_type}")
            
            # TIMING: Cache lookup
            t_cache_lookup_start = time.perf_counter()
            cached_data = cache_manager.get(cache_key, data_type)
            t_cache_lookup_elapsed = (time.perf_counter() - t_cache_lookup_start) * 1000  # ms
            
            if cached_data is not None:
                if debug_level >= 3:
                    print(f"[STEP 2] Cache lookup: {t_cache_lookup_elapsed:.2f}ms")
                    print(f"         Status: ✓ CACHE HIT")
                    print(f"         Records: {len(cached_data) if hasattr(cached_data, '__len__') else '?'}")
                    t_total_elapsed = (time.perf_counter() - t_start_total) * 1000
                    print(f"[TOTAL] Request completed in {t_total_elapsed:.2f}ms (from cache)")
                    print(f"{'='*80}\n")
                elif debug or cache_config.get('debug', False):
                    print(f"[CACHE] ✓ Cache hit: {endpoint} ({len(cached_data) if hasattr(cached_data, '__len__') else '?'} records)")
                
                # ✅ CONSISTENT: Always return list format for backward compatibility
                # This ensures `if not response.get('data')` works correctly in all strategies
                if isinstance(cached_data, pd.DataFrame):
                    return {'data': cached_data.to_dict('records'), 'status': 'success'}
                return cached_data
            
            if debug_level >= 3:
                print(f"[STEP 2] Cache lookup: {t_cache_lookup_elapsed:.2f}ms")
                print(f"         Status: ❌ CACHE MISS - Proceeding to API call...")
        
        # Cache miss or caching disabled - make API call
        
        # TIMING: URL construction (for debug)
        if debug_level >= 3 or (debug and APIManager._api_key):
            t_url_start = time.perf_counter()
            base_url = "https://restapi.ivolatility.com"
            url_params = {}
            for key, value in kwargs.items():
                clean_key = key.rstrip('_') if key.endswith('_') else key
                url_params[clean_key] = value
            
            params_str = "&".join([f"{k}={v}" for k, v in url_params.items()])
            full_url = f"{base_url}{endpoint}?apiKey={APIManager._api_key}&{params_str}"
            t_url_elapsed = (time.perf_counter() - t_url_start) * 1000
            
            if debug_level >= 3:
                print(f"[STEP 3] URL construction: {t_url_elapsed:.2f}ms")
                print(f"[API URL] {full_url}")
            else:
                print(f"\n[API] Full URL:")
                print(f"[API] {full_url}\n")
        
        # TIMING: API call execution
        t_api_start = time.perf_counter()
        method = APIManager.get_method(endpoint)
        response = method(**kwargs)
        t_api_elapsed = (time.perf_counter() - t_api_start) * 1000  # ms
        
        if debug_level >= 3:
            print(f"[STEP 4] API call execution: {t_api_elapsed:.2f}ms")
            print(f"         Response received: {type(response)}")
        
        # TIMING: Response normalization
        t_normalize_start = time.perf_counter()
        normalized = APIHelper.normalize_response(response, debug=debug)
        t_normalize_elapsed = (time.perf_counter() - t_normalize_start) * 1000  # ms
        
        if debug_level >= 3:
            print(f"[STEP 5] Response normalization: {t_normalize_elapsed:.2f}ms")
            if normalized and 'data' in normalized:
                data_len = len(normalized['data']) if hasattr(normalized.get('data'), '__len__') else '?'
                print(f"         Normalized data records: {data_len}")
            else:
                print(f"         Status: Failed to normalize")
        
        if normalized is None and debug:
            print(f"[api_call] Failed to get data")
            print(f"[api_call] Endpoint: {endpoint}")
            print(f"[api_call] Params: {kwargs}")
        
        # Save to cache if enabled and data is valid
        if use_cache and normalized is not None and cache_manager is not None:
            # Convert dict response to DataFrame for caching
            if isinstance(normalized, dict) and 'data' in normalized:
                try:
                    # TIMING: DataFrame conversion
                    t_df_start = time.perf_counter()
                    cache_data = pd.DataFrame(normalized['data'])
                    t_df_elapsed = (time.perf_counter() - t_df_start) * 1000  # ms
                    
                    if debug_level >= 3:
                        print(f"[STEP 6] DataFrame conversion: {t_df_elapsed:.2f}ms")
                        print(f"         Shape: {cache_data.shape}")
                    
                    if len(cache_data) > 0:  # Only cache non-empty data
                        # TIMING: Cache save
                        t_cache_save_start = time.perf_counter()
                        cache_manager.set(cache_key, cache_data, data_type)
                        t_cache_save_elapsed = (time.perf_counter() - t_cache_save_start) * 1000  # ms
                        
                        if debug_level >= 3:
                            print(f"[STEP 7] Cache save: {t_cache_save_elapsed:.2f}ms")
                            print(f"         Saved {len(cache_data)} records to {data_type} cache")
                        elif debug or cache_config.get('debug', False):
                            print(f"[CACHE] 💾 Saved to cache: {endpoint} ({len(cache_data)} records)")
                    else:
                        if debug or cache_config.get('debug', False):
                            print(f"[CACHE] ⚠️ Skipped caching empty data: {endpoint}")
                except Exception as e:
                    if debug or cache_config.get('debug', False):
                        print(f"[CACHE] ❌ Error converting to cache format: {e}")
        
        # TIMING: Total elapsed
        t_total_elapsed = (time.perf_counter() - t_start_total) * 1000  # ms
        
        if debug_level >= 3:
            print(f"[TOTAL] Request completed in {t_total_elapsed:.2f}ms")
            print(f"{'='*80}\n")
        
        return normalized
    
    except Exception as e:
        # Re-raise network errors for retry logic
        from http.client import RemoteDisconnected
        from requests.exceptions import ConnectionError, Timeout, RequestException
        
        if isinstance(e, (RemoteDisconnected, ConnectionError, Timeout, RequestException)):
            raise  # Let retry logic handle it
        
        # Log and return None for other errors
        if debug:
            print(f"[api_call] Exception: {e}")
            print(f"[api_call] Endpoint: {endpoint}")
            print(f"[api_call] Params: {kwargs}")
        return None


# ============================================================
# API RESPONSE HELPERS
# ============================================================
def get_api_data(response, as_dataframe=True):
    """
    Universal helper to extract data from api_call response.
    Works with both list and DataFrame formats from cache.
    
    Args:
        response: Response dict from api_call()
        as_dataframe: If True (default), always return DataFrame. 
                      If False, return list of dicts.
    
    Returns:
        DataFrame/list or None if no valid data
    
    Example:
        # Get stock data as DataFrame
        stock_df = get_api_data(api_call('/equities/eod/stock-prices', ...))
        if stock_df is None:
            print("No data!")
        
        # Get as list of dicts
        records = get_api_data(response, as_dataframe=False)
    """
    if response is None:
        return None
    
    data = response.get('data')
    if data is None:
        return None
    
    # Handle DataFrame (from cache)
    if isinstance(data, pd.DataFrame):
        if data.empty:
            return None
        return data if as_dataframe else data.to_dict('records')
    
    # Handle list (from API)
    if not data:  # empty list
        return None
    
    return pd.DataFrame(data) if as_dataframe else data


def is_api_response_valid(response):
    """
    Check if api_call response contains valid non-empty data.
    Works with both list and DataFrame formats.
    
    Args:
        response: Response dict from api_call()
    
    Returns:
        bool: True if response contains valid non-empty data
    
    Example:
        response = api_call('/equities/eod/stock-prices', ...)
        if not is_api_response_valid(response):
            print("No data available!")
            return
        
        # Safe to use response['data'] now
        df = pd.DataFrame(response['data'])
    """
    if response is None:
        return False
    
    data = response.get('data')
    if data is None:
        return False
    
    if isinstance(data, pd.DataFrame):
        return not data.empty
    
    return bool(data)


# ============================================================
# OPTIONS DATA HELPERS
# ============================================================
def collect_garbage(label="Cleanup", debug=False):
    """
    Perform garbage collection with optional memory logging
    
    Runs multiple GC passes and logs memory freed (if debug=True).
    Useful for managing memory in long-running backtests and optimization loops.
    
    Args:
        label (str): Label for the log message (e.g., "Initial", "Day 10", "Intraday")
        debug (bool): Print memory usage info (default: False)
    
    Returns:
        dict: {
            'mem_before': float,  # Memory before GC (MB)
            'mem_after': float,   # Memory after GC (MB)
            'freed': float        # Memory freed (MB)
        }
    
    Examples:
        # Silent cleanup
        collect_garbage()
        
        # With logging
        collect_garbage("Initial cleanup", debug=True)
        # Output: [GC] Initial cleanup: freed 45.2 MB (was 612.3 MB, now 567.1 MB)
        
        # In loop
        for idx, date in enumerate(trading_days):
            if idx % 10 == 0:
                collect_garbage(f"Day {idx}", debug=config.get('debuginfo', 0) >= 1)
    """
    import gc
    import psutil
    
    process = psutil.Process()
    mem_before = process.memory_info().rss / 1024 / 1024  # MB
    
    # Multiple GC passes (catches circular refs)
    for _ in range(3):
        gc.collect()
    
    mem_after = process.memory_info().rss / 1024 / 1024
    freed = mem_before - mem_after
    
    if debug:
        print(f"\033[90m[GC] {label}: freed {freed:.1f} MB (was {mem_before:.1f} MB, now {mem_after:.1f} MB)\033[0m")
    
    return {
        'mem_before': mem_before,
        'mem_after': mem_after,
        'freed': freed
    }


def safe_get_greek(option_data, greek_name):
    """
    Safely extract Greek value from option data (EOD or intraday format)
    
    This function automatically detects the data format (EOD vs intraday) and
    tries multiple possible field name variations to extract Greek values.
    
    Args:
        option_data: Option data dict/Series (from EOD or intraday API)
        greek_name: Name of the Greek to extract (e.g., 'vega', 'theta', 'delta', 'gamma')
    
    Returns:
        float: Greek value if found, None otherwise
    
    Examples:
        >>> call_vega = safe_get_greek(call_eod, 'vega')
        >>> call_theta = safe_get_greek(call_eod, 'theta')
        >>> put_delta = safe_get_greek(put_data, 'delta')
    """
    if option_data is None:
        return None

    # Auto-detect data type
    is_intraday = False
    try:
        if any(key in option_data for key in ['optionBidPrice', 'optionAskPrice', 'optionStrike', 'optionIv', 'optionType']):
            is_intraday = True
        elif hasattr(option_data, 'get'):
            if any(option_data.get(key) is not None for key in ['optionBidPrice', 'optionAskPrice', 'optionStrike', 'optionIv']):
                is_intraday = True
    except (KeyError, TypeError, AttributeError):
        pass

    # Build possible field names
    if is_intraday:
        possible_names = [
            f'option{greek_name.capitalize()}',  # e.g., 'optionVega', 'optionTheta'
            greek_name,                           # e.g., 'vega', 'theta'
        ]
    else:
        possible_names = [
            greek_name,                           # e.g., 'vega', 'theta' (EOD format)
            f'option{greek_name.capitalize()}',  # e.g., 'optionVega', 'optionTheta' (fallback)
        ]

    # Try direct access
    for name in possible_names:
        try:
            if name in option_data:
                value = option_data[name]
                if value is not None and pd.notna(value):
                    return float(value)
        except (KeyError, TypeError):
            continue

    # Try .get() method
    if hasattr(option_data, 'get'):
        for name in possible_names:
            try:
                value = option_data.get(name)
                if value is not None and pd.notna(value):
                    return float(value)
            except (TypeError, AttributeError):
                continue

    return None


# ============================================================
# BACKTEST RESULTS
# ============================================================
class BacktestResults:
    """Universal container for backtest results"""
    
    def __init__(self, equity_curve, equity_dates, trades, initial_capital, 
                 config, benchmark_prices=None, benchmark_symbol='SPY',
                 daily_returns=None, debug_info=None):
        
        self.equity_curve = equity_curve
        self.equity_dates = equity_dates
        self.trades = trades
        self.initial_capital = initial_capital
        self.final_capital = equity_curve[-1] if len(equity_curve) > 0 else initial_capital
        self.config = config
        self.benchmark_prices = benchmark_prices
        self.benchmark_symbol = benchmark_symbol
        self.debug_info = debug_info if debug_info else []
        
        if daily_returns is None and len(equity_curve) > 1:
            self.daily_returns = [
                (equity_curve[i] - equity_curve[i-1]) / equity_curve[i-1]
                for i in range(1, len(equity_curve))
            ]
        else:
            self.daily_returns = daily_returns if daily_returns else []
        
        self.max_drawdown = self._calculate_max_drawdown()
    
    def _calculate_max_drawdown(self):
        if len(self.equity_curve) < 2:
            return 0
        running_max = np.maximum.accumulate(self.equity_curve)
        drawdowns = (np.array(self.equity_curve) - running_max) / running_max * 100
        return abs(np.min(drawdowns))


# ============================================================
# STOP-LOSS MANAGER (ENHANCED VERSION WITH COMBINED STOP)
# ============================================================
class StopLossManager:
    """
    Enhanced stop-loss manager with COMBINED STOP support
    
    NEW STOP TYPE:
    - combined: Requires BOTH pl_loss AND directional conditions (from code 2)
    """
    
    def __init__(self, config=None, cache_config=None, debuginfo=0):
        """
        Initialize StopLossManager with optional config for intraday support
        
        Args:
            config: Stop-loss configuration dict (contains directional_settings)
            cache_config: Cache configuration for API calls
            debuginfo: Debug level (0=off, 1=basic, 2=detailed)
        """
        self.positions = {}
        self.config = config or {}
        self.cache_config = cache_config or {}
        
        # Debug level (0=off, 1=basic, 2=detailed)
        self.debuginfo = debuginfo
    
    def add_position(self, position_id, entry_price, entry_date, stop_type='fixed_pct', 
                    stop_value=0.05, atr=None, trailing_distance=None, use_pnl_pct=False,
                    is_short_bias=False, **kwargs):
        """
        Add position with stop-loss
        
        NEW for combined stop:
            stop_type='combined'
            stop_value={'pl_loss': 0.05, 'directional': 0.03}
        """
        self.positions[position_id] = {
            'entry_price': entry_price,
            'entry_date': entry_date,
            'stop_type': stop_type,
            'stop_value': stop_value,
            'atr': atr,
            'trailing_distance': trailing_distance,
            'highest_price': entry_price if not use_pnl_pct else 0,
            'lowest_price': entry_price if not use_pnl_pct else 0,
            'max_profit': 0,
            'use_pnl_pct': use_pnl_pct,
            'is_short_bias': is_short_bias,
            **kwargs  # Store additional parameters for combined stop
        }
    
    def check_stop(self, position_id, current_price, current_date, position_type='LONG', **kwargs):
        """
        Check if stop-loss triggered
        
        NEW: Supports 'combined' stop type
        Returns: (triggered, stop_level, stop_type, intraday_data)
                 intraday_data is a dict with fields for CSV export (or None)
        """
        if position_id not in self.positions:
            return False, None, None, None
        
        pos = self.positions[position_id]
        stop_type = pos['stop_type']
        use_pnl_pct = pos.get('use_pnl_pct', False)
        
        # Update tracking
        if use_pnl_pct:
            pnl_pct = current_price
            pos['highest_price'] = max(pos['highest_price'], pnl_pct)
            pos['lowest_price'] = min(pos['lowest_price'], pnl_pct)
            pos['max_profit'] = max(pos['max_profit'], pnl_pct)
        else:
            if position_type == 'LONG':
                pos['highest_price'] = max(pos['highest_price'], current_price)
                current_profit = current_price - pos['entry_price']
            else:
                pos['lowest_price'] = min(pos['lowest_price'], current_price)
                current_profit = pos['entry_price'] - current_price
            
            pos['max_profit'] = max(pos['max_profit'], current_profit)
        
        # Add current_date to kwargs for methods that need it (directional, combined)
        # current_date is a positional parameter but needs to be in kwargs for intraday API calls
        extended_kwargs = kwargs.copy()
        extended_kwargs['current_date'] = current_date
        
        # Route to appropriate check method
        if stop_type == 'fixed_pct':
            if use_pnl_pct:
                triggered, level, stype = self._check_fixed_pct_stop_pnl(pos, current_price)
            else:
                triggered, level, stype = self._check_fixed_pct_stop(pos, current_price, position_type)
            return triggered, level, stype, None
        
        elif stop_type == 'trailing':
            if use_pnl_pct:
                triggered, level, stype = self._check_trailing_stop_pnl(pos, current_price)
            else:
                triggered, level, stype = self._check_trailing_stop(pos, current_price, position_type)
            return triggered, level, stype, None
        
        elif stop_type == 'time_based':
            triggered, level, stype = self._check_time_stop(pos, current_date)
            return triggered, level, stype, None
        
        elif stop_type == 'volatility':
            triggered, level, stype = self._check_volatility_stop(pos, current_price, position_type)
            return triggered, level, stype, None
        
        elif stop_type == 'pl_loss':
            triggered, level, stype = self._check_pl_loss_stop(pos, extended_kwargs)
            return triggered, level, stype, None
        
        elif stop_type == 'directional':
            triggered, level, stype = self._check_directional_stop(pos, extended_kwargs)
            # Extract intraday fields from extended_kwargs (they were added by _check_directional_stop)
            intraday_data = self._extract_intraday_fields(extended_kwargs) if triggered else None
            return triggered, level, stype, intraday_data
        
        # NEW: COMBINED STOP (requires BOTH conditions)
        elif stop_type == 'combined':
            triggered, level, stype = self._check_combined_stop(pos, extended_kwargs)
            # Extract intraday fields (combined uses directional internally)
            intraday_data = self._extract_intraday_fields(extended_kwargs) if triggered else None
            return triggered, level, stype, intraday_data
        
        else:
            return False, None, None, None
    
    def _extract_intraday_fields(self, kwargs):
        """
        Extract intraday fields from kwargs for CSV export
        
        Returns dict with fields like stock_stop_trigger_time, intraday_trigger_price, etc.
        """
        intraday_data = {}
        
        # Map from kwargs field names to CSV column names
        field_mapping = {
            'intraday_trigger_time': 'stock_stop_trigger_time',
            'intraday_trigger_price': 'stock_stop_trigger_price',
            'stock_stop_trigger_price': 'stock_stop_trigger_price',  # Direct mapping for EOD fallback
            'intraday_trigger_bid': 'stock_stop_trigger_bid',
            'intraday_trigger_ask': 'stock_stop_trigger_ask',
            'intraday_trigger_bid_time': 'stock_stop_trigger_bid_time',
            'intraday_trigger_ask_time': 'stock_stop_trigger_ask_time',
            'intraday_bar_index': 'intraday_bar_index',
            'intraday_total_bars': 'intraday_data_points',
            'intraday_volume': 'intraday_volume',
            'breach_direction': 'breach_direction',  # 🆕 'high' or 'low'
            'stop_level_high': 'stop_level_high',  # 🆕
            'stop_level_low': 'stop_level_low',  # 🆕
            'intraday_data_available': 'intraday_data_available',  # Set by _check_directional_stop
        }
        
        for kwarg_field, csv_field in field_mapping.items():
            if kwarg_field in kwargs:
                intraday_data[csv_field] = kwargs[kwarg_field]
        
        # Add derived fields
        if intraday_data:
            # ✅ intraday_data_available already copied from kwargs via field_mapping
            # Use breach_direction to create stop_triggered_by field
            breach_dir = kwargs.get('breach_direction', 'unknown')
            intraday_data['stop_triggered_by'] = f'directional_{breach_dir}'  # e.g. 'directional_high' or 'directional_low'
        
        return intraday_data if intraday_data else None
    
    # ========================================================
    # EXISTING STOP METHODS (unchanged)
    # ========================================================
    
    def _check_fixed_pct_stop(self, pos, current_price, position_type):
        """Fixed percentage stop-loss (price-based)"""
        entry = pos['entry_price']
        stop_pct = pos['stop_value']
        
        if position_type == 'LONG':
            stop_level = entry * (1 - stop_pct)
            triggered = current_price <= stop_level
        else:
            stop_level = entry * (1 + stop_pct)
            triggered = current_price >= stop_level
        
        return triggered, stop_level, 'fixed_pct'
    
    def _check_fixed_pct_stop_pnl(self, pos, pnl_pct):
        """Fixed percentage stop-loss (P&L%-based for options)"""
        stop_pct = pos['stop_value']
        stop_level = -stop_pct * 100
        
        triggered = pnl_pct <= stop_level
        
        return triggered, stop_level, 'fixed_pct'
    
    def _check_trailing_stop(self, pos, current_price, position_type):
        """Trailing stop-loss (price-based)"""
        if pos['trailing_distance'] is None:
            pos['trailing_distance'] = pos['stop_value']
        
        distance = pos['trailing_distance']
        
        if position_type == 'LONG':
            stop_level = pos['highest_price'] * (1 - distance)
            triggered = current_price <= stop_level
        else:
            stop_level = pos['lowest_price'] * (1 + distance)
            triggered = current_price >= stop_level
        
        return triggered, stop_level, 'trailing'
    
    def _check_trailing_stop_pnl(self, pos, pnl_pct):
        """Trailing stop-loss (P&L%-based for options)"""
        if pos['trailing_distance'] is None:
            pos['trailing_distance'] = pos['stop_value']
        
        distance = pos['trailing_distance'] * 100
        
        stop_level = pos['highest_price'] - distance
        
        triggered = pnl_pct <= stop_level
        
        return triggered, stop_level, 'trailing'
    
    def _check_time_stop(self, pos, current_date):
        """Time-based stop"""
        days_held = (current_date - pos['entry_date']).days
        max_days = pos['stop_value']
        
        triggered = days_held >= max_days
        return triggered, None, 'time_based'
    
    def _check_volatility_stop(self, pos, current_price, position_type):
        """ATR-based stop"""
        if pos['atr'] is None:
            return False, None, None
        
        entry = pos['entry_price']
        atr_multiplier = pos['stop_value']
        stop_distance = pos['atr'] * atr_multiplier
        
        if position_type == 'LONG':
            stop_level = entry - stop_distance
            triggered = current_price <= stop_level
        else:
            stop_level = entry + stop_distance
            triggered = current_price >= stop_level
        
        return triggered, stop_level, 'volatility'
    
    def _check_pl_loss_stop(self, pos, kwargs):
        """Stop-loss based on actual P&L"""
        pnl_pct = kwargs.get('pnl_pct')
        
        if pnl_pct is None:
            # Fallback: calculate P&L% manually
            current_pnl = kwargs.get('current_pnl', 0)
            total_cost = kwargs.get('total_cost', pos.get('total_cost', 1))
            
            # ✅ For CREDIT strategies, use max_risk as denominator
            # ✅ For DEBIT strategies, use total_cost (premium paid)
            is_credit = total_cost < 0
            
            if is_credit:
                # CREDIT: P&L% relative to capital at risk (max_risk)
                max_risk = pos.get('entry_max_risk') or pos.get('max_risk', abs(total_cost))
                pnl_pct = (current_pnl / max_risk) * 100 if max_risk > 0 else 0
            else:
                # DEBIT: P&L% relative to premium paid
                pnl_pct = (current_pnl / abs(total_cost)) * 100 if total_cost != 0 else 0
        
        stop_threshold = -pos['stop_value'] * 100
        triggered = pnl_pct <= stop_threshold
        
        return triggered, stop_threshold, 'pl_loss'
    
    def _check_directional_stop(self, pos, kwargs):
        """
        Stop-loss based on underlying price movement
        
        NEW: TWO-STEP CHECK with INTRADAY support
        - STEP 1: Check EOD High/Low for breach (fast, no API)
        - STEP 2: If breached → load intraday bars for exact timing
        
        Modes:
        - 'eod_only': Use only EOD High/Low (no intraday)
        - 'auto': Try intraday, fallback to EOD if unavailable (RECOMMENDED)
        - 'minute': Require intraday (error if unavailable)
        """
        # Extract directional settings from config
        dir_settings = self.config.get('directional_settings', {})
        intraday_mode = dir_settings.get('intraday_mode', 'auto')
        minute_interval = dir_settings.get('minute_interval', 'MINUTE_1')
        min_days = dir_settings.get('min_days_before_check', 2)
        debug = dir_settings.get('debug', False)
        
        # Check position age
        current_date = kwargs.get('current_date')
        if current_date and hasattr(pos['entry_date'], 'date'):
            entry_date = pos['entry_date'].date() if hasattr(pos['entry_date'], 'date') else pos['entry_date']
            current_date_obj = current_date.date() if hasattr(current_date, 'date') else current_date
            days_held = (current_date_obj - entry_date).days
        elif current_date:
            days_held = (current_date - pos['entry_date']).days
        else:
            days_held = min_days  # Skip check if no date
        
        if days_held < min_days:
            return False, None, 'directional'
        
        # Get underlying prices
        entry_price = kwargs.get('underlying_entry_price', pos.get('underlying_entry_price'))
        eod_close = kwargs.get('underlying_price')
        eod_high = kwargs.get('underlying_high')
        eod_low = kwargs.get('underlying_low')
        
        if entry_price is None or entry_price == 0:
            return False, None, 'directional'
        
        # Get threshold and bias
        threshold = pos['stop_value']
        is_short_bias = pos.get('is_short_bias', False)
        
        # Calculate stop levels
        # For Iron Condor and similar strategies, check BOTH directions
        # For long-only or short-only strategies, check only one direction
        if is_short_bias:
            stop_high = entry_price * (1 + threshold)
            stop_low = entry_price * (1 - threshold)
        else:
            # For neutral strategies (Iron Condor), check both directions
            stop_low = entry_price * (1 - threshold)
            stop_high = entry_price * (1 + threshold)
        
        # ========================================
        # STEP 1: CHECK EOD H/L FOR BREACH
        # ========================================
        eod_breach_direction = None  # Track which level was breached
        
        if eod_high is None or eod_low is None:
            # No H/L data → fallback to close only
            if is_short_bias:
                if eod_close >= stop_high:
                    eod_breach = True
                    eod_breach_direction = 'high'
                elif eod_close <= stop_low:
                    eod_breach = True
                    eod_breach_direction = 'low'
                else:
                    eod_breach = False
            else:
                if eod_close <= stop_low:
                    eod_breach = True
                    eod_breach_direction = 'low'
                else:
                    eod_breach = False
        else:
            # Use H/L for accurate check
            if is_short_bias:
                if eod_high >= stop_high:
                    eod_breach = True
                    eod_breach_direction = 'high'
                elif eod_low <= stop_low:
                    eod_breach = True
                    eod_breach_direction = 'low'
                else:
                    eod_breach = False
            else:
                # For neutral strategies (Iron Condor), check BOTH directions
                if eod_high >= stop_high:
                    eod_breach = True
                    eod_breach_direction = 'high'
                elif eod_low <= stop_low:
                    eod_breach = True
                    eod_breach_direction = 'low'
                else:
                    eod_breach = False
        
        # If no breach → stop NOT triggered
        if not eod_breach:
            return False, threshold * 100, 'directional'
        
        # ========================================
        # STEP 2: BREACH DETECTED → INTRADAY CHECK
        # ========================================
        
        # MODE: 'eod_only' → trigger immediately with EOD breach direction
        if intraday_mode == 'eod_only':
            # Store EOD breach details
            kwargs['breach_direction'] = eod_breach_direction
            kwargs['stop_level_high'] = stop_high if stop_high else None
            kwargs['stop_level_low'] = stop_low
            kwargs['intraday_data_available'] = False  # Using EOD only
            
            # 🔍 DEBUG: Show directional stop details (level 2)
            if self.debuginfo >= 2:
                move_pct = ((eod_close - entry_price) / entry_price) * 100
                # Show which level triggered (High or Low)
                trigger_level = "HIGH" if eod_breach_direction == 'high' else "LOW"
                trigger_price = eod_high if eod_breach_direction == 'high' else eod_low
                print(f"    🚨 DIRECTIONAL STOP: Entry=${entry_price:.2f}, {trigger_level}=${trigger_price:.2f}, Close=${eod_close:.2f}")
                print(f"       Move to {trigger_level}: {((trigger_price - entry_price) / entry_price) * 100:+.2f}%, Threshold=±{threshold*100:.2f}%")
            
            if debug:
                print(f"  [Directional] EOD breach → triggered (eod_only mode), direction={eod_breach_direction}")
            return True, threshold * 100, 'directional'
        
        # MODE: 'auto' or 'minute' → try to load intraday
        try:
            symbol = pos.get('symbol', kwargs.get('symbol'))
            if symbol is None:
                # No symbol → fallback to EOD
                if intraday_mode == 'minute':
                    raise ValueError("Symbol required for intraday check")
                return True, threshold * 100, 'directional'
            
            # Load intraday data
            from ivolatility_backtesting import api_call  # Import here to avoid circular imports
            intraday_data = api_call(
                '/equities/intraday/stock-prices',
                self.cache_config,
                symbol=symbol,
                date=current_date.strftime('%Y-%m-%d') if hasattr(current_date, 'strftime') else str(current_date),
                minuteType=minute_interval
            )
            
            if intraday_data and 'data' in intraday_data:
                intraday_bars = intraday_data['data']
                
                # Sort by lastDateTime
                intraday_bars.sort(key=lambda x: x.get('lastDateTime', ''))
                
                if debug:
                    print(f"  [Directional] Loaded {len(intraday_bars)} intraday bars")
                
                # Check each bar for stop trigger
                for idx, bar in enumerate(intraday_bars):
                    last_price = bar.get('lastPrice')
                    last_time = bar.get('lastDateTime')
                    
                    if last_price is None or last_time is None:
                        continue
                    
                    # Check if this bar triggered the stop
                    triggered_this_bar = False
                    breach_direction = None  # 'up' or 'down'
                    
                    if is_short_bias:
                        if last_price >= stop_high:
                            triggered_this_bar = True
                            breach_direction = 'high'  # Price breached UPPER stop (adverse for short)
                        elif last_price <= stop_low:
                            triggered_this_bar = True
                            breach_direction = 'low'  # Price breached LOWER stop (adverse for short)
                    else:
                        if last_price <= stop_low:
                            triggered_this_bar = True
                            breach_direction = 'low'  # Price breached LOWER stop (adverse for long)
                    
                    # If triggered → save details and return
                    if triggered_this_bar:
                        # Store intraday details in kwargs for CSV export
                        kwargs['intraday_trigger_time'] = last_time
                        kwargs['intraday_trigger_price'] = last_price
                        kwargs['intraday_trigger_bid'] = bar.get('bidPrice')
                        kwargs['intraday_trigger_ask'] = bar.get('askPrice')
                        kwargs['intraday_trigger_bid_time'] = bar.get('bidDateTime')
                        kwargs['intraday_trigger_ask_time'] = bar.get('askDateTime')
                        kwargs['intraday_bar_index'] = idx
                        kwargs['intraday_total_bars'] = len(intraday_bars)
                        kwargs['intraday_volume'] = bar.get('volume')
                        kwargs['breach_direction'] = breach_direction  # 🆕 ДОБАВЛЕНО: 'high' or 'low'
                        kwargs['stop_level_high'] = stop_high if stop_high else None  # 🆕
                        kwargs['stop_level_low'] = stop_low  # 🆕
                        
                        # 🔍 DEBUG: Show intraday directional stop details (level 2)
                        if self.debuginfo >= 2:
                            trigger_level = "HIGH" if breach_direction == 'high' else "LOW"
                            print(f"    🚨 DIRECTIONAL STOP (Intraday): Entry=${entry_price:.2f}, {trigger_level}=${last_price:.2f} @ {last_time}")
                            print(f"       Move to {trigger_level}: {((last_price - entry_price) / entry_price) * 100:+.2f}%, Threshold=±{threshold*100:.2f}%")
                        
                        if debug:
                            print(f"  [Directional] Stop triggered at {last_time}, price={last_price:.2f}, direction={breach_direction}")
                        
                        return True, threshold * 100, 'directional'
                
                # Checked all bars, but no trigger found in intraday
                # If EOD showed breach → TRIGGER using EOD data
                # (Intraday used for precise timing only, not for validation)
                if debug:
                    print(f"  [Directional] EOD breach confirmed, using EOD timing (intraday not precise), direction={eod_breach_direction}")
                
                # Use EOD data as fallback
                kwargs['breach_direction'] = eod_breach_direction  # ✅ FIX: use eod_breach_direction!
                kwargs['stop_level_high'] = stop_high if stop_high else None
                kwargs['stop_level_low'] = stop_low
                kwargs['intraday_data_available'] = False
                
                # Set trigger price from EOD H/L
                if eod_breach_direction == 'high':
                    kwargs['stock_stop_trigger_price'] = eod_high
                elif eod_breach_direction == 'low':
                    kwargs['stock_stop_trigger_price'] = eod_low
                
                # 🔍 DEBUG: Show EOD fallback directional stop details (level 2)
                if self.debuginfo >= 2:
                    trigger_level = "HIGH" if eod_breach_direction == 'high' else "LOW"
                    trigger_price = eod_high if eod_breach_direction == 'high' else eod_low
                    print(f"    🚨 DIRECTIONAL STOP (EOD fallback): Entry=${entry_price:.2f}, {trigger_level}=${trigger_price:.2f}, Close=${eod_close:.2f}")
                    print(f"       Move to {trigger_level}: {((trigger_price - entry_price) / entry_price) * 100:+.2f}%, Threshold=±{threshold*100:.2f}%")
                
                return True, threshold * 100, 'directional'
            
            else:
                # No intraday data available
                if intraday_mode == 'minute':
                    raise ValueError("Intraday data required but not available")
                else:
                    # MODE 'auto' → fallback to EOD
                    kwargs['breach_direction'] = eod_breach_direction
                    kwargs['stop_level_high'] = stop_high if stop_high else None
                    kwargs['stop_level_low'] = stop_low
                    kwargs['intraday_data_available'] = False
                    
                    # 🔍 DEBUG: Show no-intraday directional stop details (level 2)
                    if self.debuginfo >= 2:
                        # Show which level triggered (High or Low)
                        trigger_level = "HIGH" if eod_breach_direction == 'high' else "LOW"
                        trigger_price = eod_high if eod_breach_direction == 'high' else eod_low
                        print(f"    🚨 DIRECTIONAL STOP (No intraday): Entry=${entry_price:.2f}, {trigger_level}=${trigger_price:.2f}, Close=${eod_close:.2f}")
                        print(f"       Move to {trigger_level}: {((trigger_price - entry_price) / entry_price) * 100:+.2f}%, Threshold=±{threshold*100:.2f}%")
                    
                    if debug:
                        print(f"  [Directional] Intraday unavailable → fallback to EOD, direction={eod_breach_direction}")
                    return True, threshold * 100, 'directional'
        
        except Exception as e:
            # Error loading intraday
            if intraday_mode == 'minute':
                # Strict mode → propagate error
                raise
            else:
                # MODE 'auto' → fallback to EOD
                kwargs['breach_direction'] = eod_breach_direction
                kwargs['stop_level_high'] = stop_high if stop_high else None
                kwargs['stop_level_low'] = stop_low
                kwargs['intraday_data_available'] = False
                
                if debug:
                    print(f"  [Directional] Intraday error ({e}) → fallback to EOD")
                return True, threshold * 100, 'directional'
    
    # ========================================================
    # NEW: COMBINED STOP (REQUIRES BOTH CONDITIONS)
    # ========================================================
    
    def _check_combined_stop(self, pos, kwargs):
        """
        Combined stop: Can use OR or AND logic
        
        ✨ NEW: Supports both OR and AND logic modes:
        - OR logic: Stop if P&L loss OR directional move (more aggressive)
        - AND logic: Stop if P&L loss AND directional move (more conservative)
        
        Uses new directional logic with intraday support.
        
        Args:
            pos: Position dict with stop_value = {'pl_loss': 0.05, 'directional': 0.03, 'logic': 'or'}
            kwargs: Must contain pnl_pct, underlying_high, underlying_low
        
        Returns:
            tuple: (triggered, thresholds_dict, 'combined')
        """
        stop_config = pos['stop_value']
        
        if not isinstance(stop_config, dict):
            # Fallback: treat as simple fixed stop
            return False, None, 'combined'
        
        pl_threshold = stop_config.get('pl_loss', 0.05)
        dir_threshold = stop_config.get('directional', 0.03)
        
        # ========================================
        # NEW: Get logic mode (OR vs AND)
        # ========================================
        # Get from combined_settings in config (preferred)
        combined_settings = self.config.get('combined_settings', {})
        logic_mode = combined_settings.get('logic', 'and')  # Default: 'and' (backward compatible)
        
        # Also check stop_config for backward compatibility
        if 'logic' in stop_config:
            logic_mode = stop_config['logic']
        
        # ========================================
        # STEP 1: Check P&L condition (with fallback calculation)
        # ========================================
        pnl_pct = kwargs.get('pnl_pct')
        
        # ✨ NEW: P&L Fallback - calculate if not provided
        if pnl_pct is None:
            current_pnl = kwargs.get('current_pnl', 0)
            total_cost = kwargs.get('total_cost', pos.get('total_cost', 1))
            
            # ✅ For CREDIT strategies, use max_risk as denominator
            # ✅ For DEBIT strategies, use total_cost (premium paid)
            is_credit = total_cost < 0
            
            if is_credit:
                # CREDIT: P&L% relative to capital at risk (max_risk)
                max_risk = pos.get('entry_max_risk') or pos.get('max_risk', abs(total_cost))
                pnl_pct = (current_pnl / max_risk) * 100 if max_risk > 0 else 0
            else:
                # DEBIT: P&L% relative to premium paid
                pnl_pct = (current_pnl / abs(total_cost)) * 100 if total_cost != 0 else 0
            
            if self.debuginfo >= 2:
                print(f"[StopLoss] P&L Fallback: current_pnl={current_pnl:.2f}, "
                      f"total_cost={total_cost:.2f}, pnl_pct={pnl_pct:.2f}%")
        
        is_losing = pnl_pct <= (-pl_threshold * 100)
        
        # ✅ DETAILED DEBUG for debuginfo >= 2
        if self.debuginfo >= 2:
            print(f"[_check_combined_stop] [DEBUG2]:")
            print(f"   Logic Mode: {logic_mode.upper()}")
            print(f"   P&L: {pnl_pct:.2f}% (threshold: -{pl_threshold*100:.2f}%) → {is_losing}")
            print(f"   Dir Threshold: {dir_threshold*100:.2f}%")
        
        # ========================================
        # STEP 2: Check directional condition (with intraday support)
        # ========================================
        # Create temporary position dict with directional threshold
        temp_pos = pos.copy()
        temp_pos['stop_value'] = dir_threshold
        temp_pos['stop_type'] = 'directional'
        
        # Call _check_directional_stop (uses new two-step logic with intraday)
        dir_triggered, dir_level, dir_type = self._check_directional_stop(temp_pos, kwargs)
        
        # ✅ DETAILED DEBUG for debuginfo >= 2
        if self.debuginfo >= 2:
            underlying_entry = pos.get('underlying_entry_price')
            underlying_high = kwargs.get('underlying_high')
            underlying_low = kwargs.get('underlying_low')
            print(f"   Directional: {dir_triggered}")
            if (underlying_entry is not None and underlying_entry > 0 and 
                underlying_high is not None and underlying_low is not None):
                high_pct = ((underlying_high - underlying_entry) / underlying_entry) * 100
                low_pct = ((underlying_low - underlying_entry) / underlying_entry) * 100
                print(f"      Entry: ${underlying_entry:.2f}")
                print(f"      High: ${underlying_high:.2f} (+{high_pct:.2f}%)")
                print(f"      Low: ${underlying_low:.2f} ({low_pct:.2f}%)")
            else:
                print(f"      Underlying prices: High={underlying_high}, Low={underlying_low}, Entry={underlying_entry}")
        
        # ========================================
        # STEP 3: Combine results based on logic mode
        # ========================================
        if logic_mode == 'or':
            # OR logic: Stop if EITHER condition is true
            triggered = is_losing or dir_triggered
        else:  # 'and' logic
            # AND logic: Stop if BOTH conditions are true
            triggered = is_losing and dir_triggered
        
        # Return detailed thresholds for reporting
        thresholds = {
            'pl_threshold': -pl_threshold * 100,
            'dir_threshold': dir_threshold * 100,
            'actual_pnl_pct': pnl_pct,
            'pl_condition': is_losing,
            'dir_condition': dir_triggered,
            'logic': logic_mode
        }
        
        # 🔍 DEBUG: Show WHY combined stop triggered (level 2)
        if triggered and self.debuginfo >= 2:
            reason = []
            if is_losing:
                reason.append(f"P&L={pnl_pct:.2f}% ≤ {-pl_threshold*100:.2f}%")
            if dir_triggered:
                reason.append(f"Directional triggered")
            reason_str = " AND ".join(reason) if logic_mode == 'and' else " OR ".join(reason)
            print(f"    ⚠️  COMBINED STOP TRIGGERED: {reason_str}")
        
        return triggered, thresholds, 'combined'
    
    # ========================================================
    # UTILITY METHODS
    # ========================================================
    
    def remove_position(self, position_id):
        """Remove position from tracking"""
        if position_id in self.positions:
            del self.positions[position_id]
    
    def get_position_info(self, position_id):
        """Get position stop-loss info"""
        if position_id not in self.positions:
            return None
        
        pos = self.positions[position_id]
        return {
            'stop_type': pos['stop_type'],
            'stop_value': pos['stop_value'],
            'max_profit_before_stop': pos['max_profit']
        }


# ============================================================
# POSITION MANAGER (unchanged but compatible with combined stop)
# ============================================================
# ============================================================
# PARAMETER VALIDATION HELPER
# ============================================================
def _get_known_params_for_strategy(strategy_type):
    """
    Extract all known parameters from STRATEGIES registry.
    
    Returns set of parameter names that are valid for given strategy.
    Used for detecting unknown/unexpected parameters from AI-generated code.
    """
    # Core parameters (valid for all strategies)
    known = {
        # Position basics
        'strategy_type', 'type', 'expiration', 'dte',
        
        # Financial
        'total_cost', 'contracts', 'quantity', 'wing_width',
        
        # Greeks
        'entry_call_delta', 'entry_put_delta', 'entry_delta',
        'entry_gamma', 'entry_vega', 'entry_theta',
        
        # Strikes (multi-leg strategies)
        'short_call_strike', 'short_put_strike',
        'long_call_strike', 'long_put_strike',
        'strike', 'call_strike', 'put_strike',
        
        # Auto-calculated/applied
        'entry_dte', 'entry_profit_target',
        
        # Risk management
        'is_short_bias', 'underlying_entry_price',
        'entry_max_risk', 'entry_bp_effect',
        
        # IVs and indicators
        'call_iv_entry', 'put_iv_entry', 'iv_lean_entry',
        'entry_z_score', 'entry_signal_strength',
        'entry_iv_rank', 'entry_iv_percentile',
        
        # Stop-loss related
        'stop_type', 'stop_value',
        
        # Diagonal/Calendar specific
        'front_dte', 'back_dte', 'strike_offset',
    }
    
    # Add strategy-specific parameters from STRATEGIES registry
    if strategy_type and strategy_type in STRATEGIES:
        strategy_def = STRATEGIES[strategy_type]
        
        # Add from required_fields
        known.update(strategy_def.get('required_fields', []))
        
        # Add from config_params
        for param in strategy_def.get('config_params', []):
            if isinstance(param, dict):
                known.add(param.get('key'))
            else:
                known.add(param)
        
        # Add from parameters dict
        known.update(strategy_def.get('parameters', {}).keys())
    
    return known


def _auto_detect_strategy_type(config):
    """
    Auto-detect strategy_type from config if missing.
    
    Detection Order:
    1. Check if 'strategy_type' already in config → return as-is
    2. Analyze 'strategy_name' for keywords
    3. Analyze config parameters (e.g., z_score_entry → IV_LEAN)
    4. Fallback to 'STRADDLE' with warning
    
    Args:
        config (dict): Strategy configuration
    
    Returns:
        str: Detected strategy_type (e.g., 'IV_LEAN', 'IRON_CONDOR', 'STRADDLE')
    """
    # 1. If already present, return as-is
    if 'strategy_type' in config and config['strategy_type']:
        return config['strategy_type']
    
    # 2. Try to detect from strategy_name
    strategy_name = config.get('strategy_name', '').lower()
    
    # IV Lean keywords
    if any(keyword in strategy_name for keyword in ['iv lean', 'iv-lean', 'ivlean', 'mean reversion']):
        print("⚠️  strategy_type missing! Auto-detected: 'IV_LEAN' (from strategy_name)")
        return 'IV_LEAN'
    
    # Iron Condor keywords
    if any(keyword in strategy_name for keyword in ['iron condor', 'iron-condor', 'ironcondor', 'ic']):
        print("⚠️  strategy_type missing! Auto-detected: 'IRON_CONDOR' (from strategy_name)")
        return 'IRON_CONDOR'
    
    # Straddle keywords
    if 'straddle' in strategy_name:
        print("⚠️  strategy_type missing! Auto-detected: 'STRADDLE' (from strategy_name)")
        return 'STRADDLE'
    
    # Strangle keywords
    if 'strangle' in strategy_name:
        print("⚠️  strategy_type missing! Auto-detected: 'STRANGLE' (from strategy_name)")
        return 'STRANGLE'
    
    # Bull Put Spread keywords
    if 'bull put' in strategy_name or 'bullput' in strategy_name:
        print("⚠️  strategy_type missing! Auto-detected: 'BULL_PUT_SPREAD' (from strategy_name)")
        return 'BULL_PUT_SPREAD'
    
    # Bear Call Spread keywords
    if 'bear call' in strategy_name or 'bearcall' in strategy_name:
        print("⚠️  strategy_type missing! Auto-detected: 'BEAR_CALL_SPREAD' (from strategy_name)")
        return 'BEAR_CALL_SPREAD'
    
    # Covered Call keywords
    if 'covered call' in strategy_name or 'coveredcall' in strategy_name:
        print("⚠️  strategy_type missing! Auto-detected: 'COVERED_CALL' (from strategy_name)")
        return 'COVERED_CALL'
    
    # 3. Try to detect from config parameters
    # IV Lean specific: has z_score_entry + z_score_exit + lookback_ratio
    if all(key in config for key in ['z_score_entry', 'z_score_exit', 'lookback_ratio']):
        print("⚠️  strategy_type missing! Auto-detected: 'IV_LEAN' (from config params)")
        return 'IV_LEAN'
    
    # Iron Condor specific: has wing_width + call_delta_target + put_delta_target
    if all(key in config for key in ['wing_width', 'call_delta_target', 'put_delta_target']):
        print("⚠️  strategy_type missing! Auto-detected: 'IRON_CONDOR' (from config params)")
        return 'IRON_CONDOR'
    
    # 4. Fallback to STRADDLE with warning
    print("⚠️  WARNING: strategy_type not found in BASE_CONFIG!")
    print("⚠️  Could not auto-detect from strategy_name or parameters.")
    print("⚠️  Using fallback: 'STRADDLE'")
    print("⚠️  → Add 'strategy_type' as FIRST field in BASE_CONFIG to fix this!")
    return 'STRADDLE'


class PositionManager:
    """Universal Position Manager with automatic mode detection"""
    
    def __init__(self, config, debug=False):
        self.positions = {}
        self.closed_trades = []
        self.config = config
        self.debug = debug
        self.debuginfo = config.get('debuginfo', 0)  # ✅ Add debuginfo level
        
        # ✅ AUTO-DETECT strategy_type if missing
        if 'strategy_type' not in config or not config['strategy_type']:
            config['strategy_type'] = _auto_detect_strategy_type(config)
        
        # Cumulative P&L tracking
        self.cumulative_pnl = 0.0
        self.initial_capital = config.get('initial_capital', 100000)
        
        # ========================================================
        # FORWARD-FILL: Cache last known prices for missing data
        # ========================================================
        # Stores last known price_data for each position to use when
        # current data is missing (weekends, holidays, data gaps)
        # Structure: {position_id: {price_data_dict}}
        self.last_known_price_data = {}
        
        # Enable/disable forward-fill (default: enabled)
        # Set to False if you want strict "skip if no data" behavior
        self.enable_forward_fill = config.get('enable_forward_fill', True)
        
        # Stop-loss enable logic:
        # 1) Respect explicit flag if provided
        # 2) Otherwise infer from stop_loss_config.enabled for convenience
        explicit_flag = config.get('stop_loss_enabled')
        sl_cfg = config.get('stop_loss_config', {})
        inferred_flag = bool(sl_cfg.get('enabled', False))

        self.sl_enabled = explicit_flag if explicit_flag is not None else inferred_flag

        if self.sl_enabled:
            self.sl_config = sl_cfg
            # Pass config, cache_config, and debuginfo for intraday support
            cache_cfg = config.get('cache_config', {})
            self.sl_manager = StopLossManager(
                config=sl_cfg, 
                cache_config=cache_cfg,
                debuginfo=config.get('debuginfo', 0)
            )
        else:
            self.sl_config = None
            self.sl_manager = None
    
    # ================================================================
    # ENTRY COST CALCULATION (wrapper for StrategyRegistry)
    # ================================================================
    def calculate_entry_cost(self, leg_data, contracts=1, is_short=None):
        """
        Calculate entry cost for current strategy (uses strategy_type from config).
        
        This is a convenience wrapper around StrategyRegistry.calculate_entry_cost()
        that automatically uses strategy_type from self.config.
        
        Args:
            leg_data: Dict with option data at entry
            contracts: Number of contracts (default=1 for per-contract calculation)
            is_short: Override for SHORT detection (True = sell to open, False = buy to open)
                     Required for strategies like STRADDLE/IV_LEAN where leg names don't have 'short_' prefix
        
        Returns:
            dict: {
                'total': Total cost (positive for DEBIT, negative for CREDIT),
                'per_leg': {leg_name: cost, ...},
                'net_credit': bool,
            }
        
        Example:
            entry_cost = position_mgr.calculate_entry_cost(
                {'call': call_data, 'put': put_data},
                contracts=2,
                is_short=True
            )
        """
        strategy_type = self.config.get('strategy_type', 'STRADDLE')
        return StrategyRegistry.calculate_entry_cost(strategy_type, leg_data, contracts, is_short)
    
    # ================================================================
    # UNIVERSAL INTRINSIC VALUE CALCULATION METHOD
    # ================================================================
    def _calculate_intrinsic_value(self, position, position_id, strategy_type, 
                                    underlying_price, strike, contracts):
        """
        Calculate intrinsic value at expiration for any strategy type.
        
        Uses STRATEGIES registry for accurate leg detection.
        Returns intrinsic_value (what we owe for CREDIT or receive for DEBIT).
        
        Args:
            position: dict with position data (strikes, legs, etc.)
            position_id: str, unique position identifier
            strategy_type: str, e.g. 'IRON_CONDOR', 'BULL_PUT_SPREAD'
            underlying_price: float, current underlying price
            strike: float, fallback strike if not in position
            contracts: int, number of contracts
            
        Returns:
            float: intrinsic value (positive = we owe, negative = we receive)
        """
        intrinsic_value = 0
        
        # Get strategy info from registry
        strategy_info = STRATEGIES.get(strategy_type, {})
        category = strategy_info.get('category', 'UNKNOWN')
        
        if 'IRON_CONDOR' in strategy_type.upper() or 'IC' in position_id.upper():
            # ========================================================
            # IRON CONDOR: Short call spread + Short put spread
            # ========================================================
            short_call = position.get('short_call_strike', 0)
            long_call = position.get('long_call_strike', 0)
            short_put = position.get('short_put_strike', 0)
            long_put = position.get('long_put_strike', 0)
            
            if self.debug:
                print(f"[INTRINSIC SETTLEMENT] {position_id} - Iron Condor:")
                print(f"   Underlying: ${underlying_price:.2f}")
                print(f"   Call spread: short ${short_call:.2f} / long ${long_call:.2f}")
                print(f"   Put spread: short ${short_put:.2f} / long ${long_put:.2f}")
            
            # Calculate intrinsic for each spread
            call_spread_loss = 0
            put_spread_loss = 0
            
            if underlying_price > short_call and short_call > 0:
                # Call side ITM - we owe the difference (capped by long call)
                call_spread_loss = min(underlying_price - short_call, long_call - short_call) if long_call > short_call else (underlying_price - short_call)
            
            if underlying_price < short_put and short_put > 0:
                # Put side ITM - we owe the difference (capped by long put)
                put_spread_loss = min(short_put - underlying_price, short_put - long_put) if long_put < short_put else (short_put - underlying_price)
            
            # Total intrinsic value we owe (as short seller)
            intrinsic_value = (call_spread_loss + put_spread_loss) * 100 * contracts
            
            if self.debug:
                print(f"   Call spread loss: ${call_spread_loss:.2f}, Put spread loss: ${put_spread_loss:.2f}")
                print(f"   Total intrinsic owed: ${intrinsic_value:.2f}")
        
        elif 'IRON_BUTTERFLY' in strategy_type.upper():
            # ========================================================
            # IRON BUTTERFLY: Short ATM straddle + Long wings
            # ========================================================
            atm_strike = position.get('atm_strike', position.get('strike', strike))
            wing_width = position.get('wing_width', 10)
            long_put = atm_strike - wing_width
            long_call = atm_strike + wing_width
            
            if self.debug:
                print(f"[INTRINSIC SETTLEMENT] {position_id} - Iron Butterfly:")
                print(f"   Underlying: ${underlying_price:.2f}, ATM: ${atm_strike:.2f}, Wing: ${wing_width:.2f}")
            
            # Calculate loss based on where underlying is
            if underlying_price <= long_put:
                intrinsic_value = wing_width * 100 * contracts  # Max loss on put side
            elif underlying_price >= long_call:
                intrinsic_value = wing_width * 100 * contracts  # Max loss on call side
            elif underlying_price < atm_strike:
                intrinsic_value = (atm_strike - underlying_price) * 100 * contracts  # Partial loss
            elif underlying_price > atm_strike:
                intrinsic_value = (underlying_price - atm_strike) * 100 * contracts  # Partial loss
            else:
                intrinsic_value = 0  # At ATM - max profit
        
        elif 'STRADDLE' in strategy_type.upper() or 'straddle' in position_id.lower():
            # ========================================================
            # STRADDLE: Call + Put at same strike
            # ========================================================
            call_intrinsic = max(0, underlying_price - strike)
            put_intrinsic = max(0, strike - underlying_price)
            intrinsic_value = (call_intrinsic + put_intrinsic) * 100 * contracts
            
            if self.debug:
                print(f"[INTRINSIC SETTLEMENT] {position_id} - Straddle:")
                print(f"   Underlying: ${underlying_price:.2f}, Strike: ${strike:.2f}")
                print(f"   Call intrinsic: ${call_intrinsic:.2f}, Put intrinsic: ${put_intrinsic:.2f}")
                print(f"   Total: ${intrinsic_value:.2f}")
        
        elif 'STRANGLE' in strategy_type.upper():
            # ========================================================
            # STRANGLE: Call and Put at different strikes
            # ========================================================
            call_strike = position.get('call_strike', strike)
            put_strike = position.get('put_strike', strike)
            call_intrinsic = max(0, underlying_price - call_strike)
            put_intrinsic = max(0, put_strike - underlying_price)
            intrinsic_value = (call_intrinsic + put_intrinsic) * 100 * contracts
        
        elif 'BULL_PUT' in strategy_type.upper():
            # ========================================================
            # BULL PUT SPREAD (CREDIT): Short higher put + Long lower put
            # ========================================================
            short_strike = position.get('short_strike', position.get('short_put_strike', strike))
            long_strike = position.get('long_strike', position.get('long_put_strike', strike - 5))
            
            short_intrinsic = max(0, short_strike - underlying_price)
            long_intrinsic = max(0, long_strike - underlying_price)
            intrinsic_value = (short_intrinsic - long_intrinsic) * 100 * contracts
            
            if self.debug:
                print(f"[INTRINSIC SETTLEMENT] {position_id} - Bull Put Spread:")
                print(f"   Underlying: ${underlying_price:.2f}, Short: ${short_strike:.2f}, Long: ${long_strike:.2f}")
                print(f"   Intrinsic owed: ${intrinsic_value:.2f}")
        
        elif 'BEAR_CALL' in strategy_type.upper():
            # ========================================================
            # BEAR CALL SPREAD (CREDIT): Short lower call + Long higher call
            # ========================================================
            short_strike = position.get('short_strike', position.get('short_call_strike', strike))
            long_strike = position.get('long_strike', position.get('long_call_strike', strike + 5))
            
            short_intrinsic = max(0, underlying_price - short_strike)
            long_intrinsic = max(0, underlying_price - long_strike)
            intrinsic_value = (short_intrinsic - long_intrinsic) * 100 * contracts
            
            if self.debug:
                print(f"[INTRINSIC SETTLEMENT] {position_id} - Bear Call Spread:")
                print(f"   Underlying: ${underlying_price:.2f}, Short: ${short_strike:.2f}, Long: ${long_strike:.2f}")
                print(f"   Intrinsic owed: ${intrinsic_value:.2f}")
        
        elif 'BULL_CALL' in strategy_type.upper():
            # ========================================================
            # BULL CALL SPREAD (DEBIT): Long lower call + Short higher call
            # ========================================================
            long_strike = position.get('long_strike', position.get('long_call_strike', strike))
            short_strike = position.get('short_strike', position.get('short_call_strike', strike + 5))
            
            long_intrinsic = max(0, underlying_price - long_strike)
            short_intrinsic = max(0, underlying_price - short_strike)
            intrinsic_value = (long_intrinsic - short_intrinsic) * 100 * contracts
            
            if self.debug:
                print(f"[INTRINSIC SETTLEMENT] {position_id} - Bull Call Spread:")
                print(f"   Underlying: ${underlying_price:.2f}, Long: ${long_strike:.2f}, Short: ${short_strike:.2f}")
                print(f"   Intrinsic received: ${intrinsic_value:.2f}")
        
        elif 'BEAR_PUT' in strategy_type.upper():
            # ========================================================
            # BEAR PUT SPREAD (DEBIT): Long higher put + Short lower put
            # ========================================================
            long_strike = position.get('long_strike', position.get('long_put_strike', strike))
            short_strike = position.get('short_strike', position.get('short_put_strike', strike - 5))
            
            long_intrinsic = max(0, long_strike - underlying_price)
            short_intrinsic = max(0, short_strike - underlying_price)
            intrinsic_value = (long_intrinsic - short_intrinsic) * 100 * contracts
            
            if self.debug:
                print(f"[INTRINSIC SETTLEMENT] {position_id} - Bear Put Spread:")
                print(f"   Underlying: ${underlying_price:.2f}, Long: ${long_strike:.2f}, Short: ${short_strike:.2f}")
                print(f"   Intrinsic received: ${intrinsic_value:.2f}")
        
        elif 'BUTTERFLY' in strategy_type.upper() and 'IRON' not in strategy_type.upper():
            # ========================================================
            # BUTTERFLY (DEBIT): Long lower + Short 2x middle + Long upper
            # ========================================================
            center_strike = position.get('center_strike', strike)
            wing_width = position.get('wing_width', 10)
            lower_strike = center_strike - wing_width
            upper_strike = center_strike + wing_width
            
            if self.debug:
                print(f"[INTRINSIC SETTLEMENT] {position_id} - Butterfly:")
                print(f"   Underlying: ${underlying_price:.2f}, Center: ${center_strike:.2f}, Wing: ${wing_width:.2f}")
            
            # Butterfly payoff
            if underlying_price <= lower_strike or underlying_price >= upper_strike:
                intrinsic_value = 0  # Outside wings - all OTM
            elif underlying_price <= center_strike:
                intrinsic_value = (underlying_price - lower_strike) * 100 * contracts
            else:
                intrinsic_value = (upper_strike - underlying_price) * 100 * contracts
        
        elif 'CREDIT_SPREAD' in strategy_type.upper() or 'DEBIT_SPREAD' in strategy_type.upper() or 'PUT_SPREAD' in strategy_type.upper() or 'CALL_SPREAD' in strategy_type.upper():
            # ========================================================
            # GENERIC VERTICAL SPREAD
            # ========================================================
            short_strike = position.get('short_strike', strike)
            long_strike = position.get('long_strike', strike)
            opt_type = position.get('opt_type', 'C')
            
            if opt_type == 'C':
                short_intrinsic = max(0, underlying_price - short_strike)
                long_intrinsic = max(0, underlying_price - long_strike)
            else:
                short_intrinsic = max(0, short_strike - underlying_price)
                long_intrinsic = max(0, long_strike - underlying_price)
            
            intrinsic_value = (short_intrinsic - long_intrinsic) * 100 * contracts
            
            if self.debug:
                print(f"[INTRINSIC SETTLEMENT] {position_id} - Vertical Spread ({opt_type}):")
                print(f"   Underlying: ${underlying_price:.2f}, Short: ${short_strike:.2f}, Long: ${long_strike:.2f}")
                print(f"   Intrinsic: ${intrinsic_value:.2f}")
        
        elif 'CALENDAR' in strategy_type.upper() or 'DIAGONAL' in strategy_type.upper():
            # ========================================================
            # CALENDAR/DIAGONAL: Cannot settle accurately
            # ========================================================
            print(f"\n⚠️  WARNING: {position_id} - Calendar/Diagonal at expiration!")
            print(f"    Back month still has time value - intrinsic settlement is APPROXIMATE")
            print(f"    RECOMMENDATION: Use 'dte_exit' or 'options-rawiv' dataset")
            
            if self.debug:
                print(f"[INTRINSIC SETTLEMENT] {position_id} - Calendar/Diagonal:")
                print(f"   Using APPROXIMATION: front month intrinsic only")
            
            # Approximation: Only front month intrinsic (back has time value)
            front_strike = position.get('front_strike', position.get('strike', strike))
            opt_type = position.get('opt_type', 'C')
            
            if opt_type == 'C':
                intrinsic_value = max(0, underlying_price - front_strike) * 100 * contracts
            else:
                intrinsic_value = max(0, front_strike - underlying_price) * 100 * contracts
        
        elif 'COVERED_CALL' in strategy_type.upper():
            # ========================================================
            # COVERED CALL: Long stock + Short call
            # ========================================================
            print(f"\n⚠️  WARNING: {position_id} - Covered Call at expiration!")
            print(f"    Calculation includes CALL obligation only (stock tracked separately)")
            print(f"    RECOMMENDATION: Verify stock position P&L is tracked independently")
            
            if self.debug:
                print(f"[INTRINSIC SETTLEMENT] {position_id} - Covered Call:")
                print(f"   Call intrinsic calculated (stock component separate)")
            
            call_strike = position.get('call_strike', position.get('short_call_strike', strike))
            call_intrinsic = max(0, underlying_price - call_strike)
            intrinsic_value = call_intrinsic * 100 * contracts  # Only call obligation
        
        else:
            # ========================================================
            # FALLBACK: Single option or unknown strategy
            # ========================================================
            opt_type = position.get('opt_type', 'C')
            if opt_type == 'C':
                intrinsic_value = max(0, underlying_price - strike) * 100 * contracts
            else:
                intrinsic_value = max(0, strike - underlying_price) * 100 * contracts
            
            if self.debug:
                print(f"[INTRINSIC SETTLEMENT] {position_id} - Single Option ({opt_type}):")
                print(f"   Underlying: ${underlying_price:.2f}, Strike: ${strike:.2f}")
                print(f"   Intrinsic: ${intrinsic_value:.2f}")
        
        return intrinsic_value
    
    def open_position(self, position_id, symbol, entry_date, entry_price, 
                      quantity, position_type=None, **kwargs):
        """
        Open position with automatic stop-loss and position_type detection.
        
        Args:
            position_type: 'LONG' or 'SHORT' (optional - auto-detected if None)
                          For options strategies, auto-detected from:
                          - strategy_type (via STRATEGIES['category'])
                          - entry_price (0 = CREDIT = SHORT)
                          - total_cost (negative = CREDIT = SHORT)
        """
        
        debug_level = self.config.get('debuginfo', 0)
        
        # ================================================================
        # 🔍 PARAMETER VALIDATION & AUTO-FIX (3-level system)
        # ================================================================
        strategy_type = kwargs.get('strategy_type')
        known_params = _get_known_params_for_strategy(strategy_type)
        unknown_params = set(kwargs.keys()) - known_params
        
        validation_summary = {
            'unknown': [],
            'auto_fixes': [],
            'warnings': []
        }
        
        # 🔍 LEVEL 1: Check for UNKNOWN parameters
        if unknown_params and debug_level >= 1:
            for param in sorted(unknown_params):
                print(f"🔍 UNKNOWN: Parameter '{param}' = {kwargs[param]}")
                print(f"   Strategy: {strategy_type or 'N/A'}")
                print(f"   This parameter is not in STRATEGIES registry.")
                print(f"   It will be stored in position but may not be used by framework.")
                validation_summary['unknown'].append(param)
        
        # 🔧 LEVEL 2: AUTO-FIX numpy types (from optimization param_grid)
        for key in list(kwargs.keys()):
            if hasattr(kwargs[key], 'item'):  # numpy.int64, numpy.float64, etc.
                old_type = type(kwargs[key]).__name__
                old_value = kwargs[key]
                try:
                    kwargs[key] = kwargs[key].item()  # Convert to Python native type
                    if debug_level >= 2:
                        print(f"🔧 AUTO-FIX: Parameter '{key}' converted from {old_type} to {type(kwargs[key]).__name__}")
                    validation_summary['auto_fixes'].append(f"{key} ({old_type}→{type(kwargs[key]).__name__})")
                except Exception as e:
                    if debug_level >= 1:
                        print(f"⚠️ WARNING: Cannot convert '{key}' from {old_type}: {e}")
                    validation_summary['warnings'].append(f"{key} (conversion failed)")
        
        # ⚙️ LEVEL 2: AUTO-CALCULATE entry_dte if missing
        if 'entry_dte' not in kwargs and 'expiration' in kwargs:
            expiration = kwargs['expiration']
            # Safe date extraction
            if hasattr(entry_date, 'date'):
                entry_date_obj = entry_date.date()
            else:
                entry_date_obj = entry_date
            
            if hasattr(expiration, 'date'):
                expiration_obj = expiration.date()
            else:
                expiration_obj = expiration
            
            kwargs['entry_dte'] = (expiration_obj - entry_date_obj).days
            
            if debug_level >= 2:
                print(f"⚙️ FRAMEWORK: Auto-calculated entry_dte = {kwargs['entry_dte']} days")
            validation_summary['auto_fixes'].append(f"entry_dte (auto-calculated)")
        
        # ⚙️ LEVEL 2: AUTO-APPLY profit_target from strategy defaults
        if 'entry_profit_target' not in kwargs and strategy_type:
            if strategy_type in STRATEGIES:
                default_target = STRATEGIES[strategy_type].get('defaults', {}).get('profit_target')
                if default_target is not None:
                    kwargs['entry_profit_target'] = default_target
                    if debug_level >= 2:
                        print(f"⚙️ FRAMEWORK: Auto-applied profit_target = {default_target:.2f} (from STRATEGIES defaults)")
                    validation_summary['auto_fixes'].append(f"entry_profit_target (default={default_target})")
        
        # 💡 LEVEL 3: Provide TIP for unknown parameters
        if unknown_params and debug_level >= 1:
            print(f"💡 TIP: If these parameters are intentional, add them to STRATEGIES['{strategy_type}']['parameters']")
            print(f"        If they are AI errors, check your prompt for hallucinations.")
        
        # ✅ Validation summary (only if something happened)
        if debug_level >= 1 and any(validation_summary.values()):
            total_issues = len(validation_summary['unknown']) + len(validation_summary['warnings'])
            total_fixes = len(validation_summary['auto_fixes'])
            if total_issues > 0 or total_fixes > 0:
                print(f"✅ Validation complete: {total_fixes} auto-fixes, {total_issues} issues")
        
        # ================================================================
        # Original validation (CRITICAL errors)
        # ================================================================
        if entry_price == 0 and self.sl_enabled:
            if 'total_cost' not in kwargs or kwargs['total_cost'] == 0:
                print(f"🚨 CRITICAL: Missing required parameter 'total_cost' for CREDIT strategy")
                raise ValueError(
                    f"\n{'='*70}\n"
                    f"ERROR: P&L% mode requires 'total_cost' parameter\n"
                    f"{'='*70}\n"
                )
        
        # ✅ BACKWARD COMPATIBILITY: If 'type' passed but 'strategy_type' not, copy type → strategy_type
        if 'strategy_type' not in kwargs and 'type' in kwargs:
            kwargs['strategy_type'] = kwargs['type']
        
        # ✅ AUTO-DETECT position_type if not provided
        if position_type is None:
            strategy_type = kwargs.get('strategy_type')
            total_cost = kwargs.get('total_cost', 0)
            
            is_credit = StrategyRegistry.is_credit_strategy(
                strategy_type=strategy_type,
                entry_price=entry_price,
                total_cost=total_cost
            )
            position_type = 'SHORT' if is_credit else 'LONG'
        
        position = {
            'id': position_id,
            'symbol': symbol,
            'entry_date': entry_date,
            'entry_price': entry_price,
            'quantity': quantity,
            'type': position_type,
            'highest_price': entry_price,
            'lowest_price': entry_price,
            **kwargs
        }
        
        if self.sl_enabled and self.sl_manager:
            sl_type = self.sl_config.get('type', 'fixed_pct')
            
            # ✅ COMBINED STOP: Extract from 'combined_settings' (dict), not 'value' (float)
            if sl_type == 'combined':
                combined_settings = self.sl_config.get('combined_settings', {})
                if combined_settings:
                    # Use combined_settings dict as sl_value
                    sl_value = combined_settings
                else:
                    # Fallback to 'value' if combined_settings missing
                    sl_value = self.sl_config.get('value', 0.05)
            else:
                # For other stop types: use 'value' (float)
                sl_value = self.sl_config.get('value', 0.05)
            
            # ✅ SAVE stop-loss params in position for debugging/export
            position['stop_type'] = sl_type
            position['stop_value'] = sl_value
            
            # 🔍 DEBUG: Log first 3 positions to verify stop-loss value (level 2)
            if self.debug and len(self.positions) <= 3 and self.config.get('debuginfo', 0) >= 2:
                # Format sl_value: dict for combined, float for others
                sl_display = sl_value if isinstance(sl_value, dict) else f"{sl_value:.4f}"
                print(f"  🔍 POSITION #{len(self.positions)}: sl_value = {sl_display}, sl_type = {sl_type}")
            
            use_pnl_pct = (entry_price == 0)
            is_short_bias = kwargs.get('is_short_bias', False)
            
            # Pass underlying_entry_price for combined stop
            self.sl_manager.add_position(
                position_id=position_id,
                entry_price=entry_price,
                entry_date=entry_date,
                stop_type=sl_type,
                stop_value=sl_value,
                atr=kwargs.get('atr', None),
                trailing_distance=self.sl_config.get('trailing_distance', None),
                use_pnl_pct=use_pnl_pct,
                is_short_bias=is_short_bias,
                underlying_entry_price=kwargs.get('underlying_entry_price')  # For combined stop
            )
        
        self.positions[position_id] = position
        
        if self.debug:
            mode = "P&L%" if entry_price == 0 else "Price"
            bias = " (SHORT BIAS)" if kwargs.get('is_short_bias') else ""
            # Light green (salad) color for OPEN events
            color_start = "\033[38;5;150m"  # Light green/salad color
            color_end = "\033[0m"           # Reset
            print(f"[PositionManager] {color_start}⚙️  OPEN {position_id}: {symbol} @ {entry_price} (Mode: {mode}{bias}){color_end}")
        
        return position
    
    def check_positions(self, current_date, price_data, underlying_price=None):
        """
        Check all positions for:
        1. Option expiration (automatic for options)
        2. Stop-loss triggers (if enabled)
        
        ✨ NEW: Automatic forward-fill for missing price data
        ✨ NEW: Intrinsic value settlement at expiration
        
        Args:
            current_date: Current trading date
            price_data: Dict of {position_id: price_info}
            underlying_price: Current underlying price (for intrinsic value settlement)
        """
        to_close = []
        
        # Store underlying price for intrinsic settlement
        self._current_underlying_price = underlying_price
        
        # ========================================================
        # FORWARD-FILL: Apply cached prices for missing data
        # ========================================================
        if self.enable_forward_fill:
            # Step 1: Update cache with current data (for positions that have data today)
            for pos_id in list(price_data.keys()):
                if pos_id in self.positions:
                    self.last_known_price_data[pos_id] = price_data[pos_id]
            
            # Step 2: Apply forward-fill for positions WITHOUT data today
            for pos_id in list(self.positions.keys()):
                if pos_id not in price_data:
                    # Use last known prices if available
                    if pos_id in self.last_known_price_data:
                        # Copy data and mark as forward-fill
                        ff_data = self.last_known_price_data[pos_id].copy() if isinstance(self.last_known_price_data[pos_id], dict) else self.last_known_price_data[pos_id]
                        if isinstance(ff_data, dict):
                            ff_data['_is_forward_fill'] = True
                        price_data[pos_id] = ff_data
                        
                        # Only print forward-fill at debug level 2+
                        if self.debug and self.debug >= 2:
                            print(f"[FORWARD-FILL] {current_date} {pos_id}: using last known prices")
        
        # ========================================================
        # 1. CHECK EXPIRATION (for all positions with expiration date)
        # ========================================================
        for position_id, position in self.positions.items():
            expiration = position.get('expiration')
            
            if expiration is not None:
                # Convert to date if needed
                if hasattr(expiration, 'date'):
                    expiration = expiration.date()
                elif isinstance(expiration, str):
                    # Handle string dates like '2024-12-20'
                    from datetime import datetime
                    try:
                        expiration = datetime.strptime(expiration, '%Y-%m-%d').date()
                    except:
                        pass
                
                # Check if expired
                current_date_normalized = current_date.date() if hasattr(current_date, 'date') else current_date
                
                if current_date_normalized >= expiration:
                    # Track if we used intrinsic value settlement
                    used_intrinsic = False
                    
                    # Check if data is forward-fill (stale) - if so, use intrinsic settlement
                    is_forward_fill = False
                    if position_id in price_data and isinstance(price_data[position_id], dict):
                        is_forward_fill = price_data[position_id].get('_is_forward_fill', False)
                    
                    # Get current price for P&L calculation
                    # Use intrinsic settlement if: no data OR data is forward-fill (stale)
                    if position_id in price_data and not is_forward_fill:
                        # DEBUG: Log market data usage
                        if self.debug and self.debug >= 2:
                            print(f"[MARKET DATA] {current_date} {position_id}: using fresh market prices")
                        
                        if isinstance(price_data[position_id], dict):
                            data = price_data[position_id]
                            current_price = data.get('price', position['entry_price'])
                            current_pnl = data.get('pnl', 0)
                            current_pnl_pct = data.get('pnl_pct')
                            
                            # ✅ If pnl_pct not provided, calculate correctly for CREDIT strategies
                            if current_pnl_pct is None and position['entry_price'] == 0:
                                # CREDIT strategy - use MAX_RISK for percentage
                                # ⚠️ CRITICAL: entry_max_risk is ALREADY TOTAL (not per-contract!)
                                max_risk_total = position.get('entry_max_risk', 0)
                                
                                # If entry_max_risk not saved, calculate from strikes (Iron Condor)
                                if max_risk_total == 0:
                                    # Try CALL strikes first
                                    long_call = position.get('long_call_strike', 0)
                                    short_call = position.get('short_call_strike', 0)
                                    
                                    # Fallback to PUT strikes if call strikes unavailable
                                    long_put = position.get('long_put_strike', 0)
                                    short_put = position.get('short_put_strike', 0)
                                    
                                    wing_width = 0
                                    if long_call > 0 and short_call > 0:
                                        wing_width = abs(long_call - short_call)
                                    elif long_put > 0 and short_put > 0:
                                        wing_width = abs(long_put - short_put)
                                    
                                    if wing_width > 0:
                                        # ✅ Use abs() because total_cost is negative for credits
                                        total_cost_per_contract = abs(position.get('total_cost', 0)) / position.get('contracts', 1)
                                        max_risk_per_contract = (wing_width * 100) - total_cost_per_contract
                                        contracts = position.get('contracts', 1)
                                        max_risk_total = max_risk_per_contract * contracts
                                
                                if max_risk_total > 0:
                                    current_pnl_pct = (current_pnl / max_risk_total) * 100
                                else:
                                    current_pnl_pct = 0
                            elif current_pnl_pct is None:
                                current_pnl_pct = 0
                        else:
                            current_price = price_data[position_id]
                            current_pnl = (current_price - position['entry_price']) * position['quantity']
                            current_pnl_pct = (current_price - position['entry_price']) / position['entry_price'] if position['entry_price'] != 0 else 0
                    
                    # Use intrinsic settlement if: no fresh data OR data is forward-fill (stale)
                    if position_id not in price_data or is_forward_fill:
                        # ========================================================
                        # INTRINSIC VALUE SETTLEMENT (no market data or stale data)
                        # ========================================================
                        # Calculate P&L based on intrinsic value at expiration
                        # This is how options actually settle on the exchange
                        
                        # DEBUG: Log why using intrinsic
                        if self.debug and self.debug >= 2:
                            reason = "no_data" if position_id not in price_data else "forward_fill"
                            print(f"[INTRINSIC SETTLEMENT] {current_date} {position_id}: reason={reason}")
                        
                        # Try to get underlying price in order of preference:
                        # 1. Current underlying price (passed to check_positions)
                        # 2. Position's underlying_exit_price (if set)
                        # 3. Position's underlying_entry_price (fallback)
                        underlying_price = (
                            self._current_underlying_price or 
                            position.get('underlying_exit_price') or 
                            position.get('underlying_entry_price', 0)
                        )
                        strike = position.get('strike', 0)
                        strategy_type = position.get('strategy_type', '')
                        contracts = position.get('contracts', 1)
                        entry_premium = abs(position.get('total_cost', 0))  # Premium received (for SELL) or paid (for BUY)
                        
                        # ================================================================
                        # CALL UNIVERSAL INTRINSIC VALUE METHOD
                        # ================================================================
                        intrinsic_value = self._calculate_intrinsic_value(
                            position=position,
                            position_id=position_id,
                            strategy_type=strategy_type,
                            underlying_price=underlying_price,
                            strike=strike,
                            contracts=contracts
                        )
                        
                        # Get strategy info for P&L calculation
                        strategy_info = STRATEGIES.get(strategy_type, {})
                        category = strategy_info.get('category', 'UNKNOWN')
                        
                        # Calculate P&L
                        # For SELL strategies: P&L = premium_received - intrinsic_value (we owe intrinsic)
                        # For BUY strategies: P&L = intrinsic_value - premium_paid
                        is_sell = 'SELL' in strategy_type.upper() or position.get('entry_price', 0) == 0
                        
                        if is_sell:
                            current_pnl = entry_premium - intrinsic_value
                            current_price = intrinsic_value / (100 * contracts) if contracts > 0 else 0
                        else:
                            current_pnl = intrinsic_value - entry_premium
                            current_price = intrinsic_value / (100 * contracts) if contracts > 0 else 0
                        
                        # Calculate P&L percentage
                        max_risk = position.get('entry_max_risk', entry_premium)
                        if max_risk > 0:
                            current_pnl_pct = (current_pnl / max_risk) * 100
                        else:
                            current_pnl_pct = 0
                        
                        if self.debug:
                            print(f"   Entry premium: ${entry_premium:.2f}, P&L: ${current_pnl:.2f} ({current_pnl_pct:.1f}%)")
                        
                        # Mark as intrinsic settlement
                        used_intrinsic = True
                    
                    # Determine stop_type: 'expiration' (market data) or 'expiration_intrinsic' (no data)
                    stop_type = 'expiration_intrinsic' if used_intrinsic else 'expiration'
                    
                    # ✅ AUTO-GENERATE close kwargs (so strategy code doesn't need to call generate_close_position_kwargs)
                    strategy_type = position.get('strategy_type', 'STRADDLE')
                    pos_data = price_data.get(position_id, {})
                    close_kwargs = StrategyRegistry.generate_close_position_kwargs(strategy_type, pos_data)
                    
                    stop_info = {
                        'position_id': position_id,
                        'symbol': position['symbol'],
                        'stop_type': stop_type,
                        'close_reason': stop_type,  # ✅ For strategy stats
                        'stat_key': 'expiration_exits',  # ✅ For strategy stats
                        'stop_level': None,
                        'current_price': current_price,
                        'pnl': current_pnl,
                        'pnl_pct': current_pnl_pct,
                        'settlement_type': 'intrinsic' if used_intrinsic else 'market',
                        **close_kwargs  # ✅ Include leg exit data automatically
                    }
                    
                    to_close.append(stop_info)
                    
                    if self.debug:
                        print(f"[PositionManager] 📅 EXPIRATION: {position_id} expired on {expiration}")
        
        # ========================================================
        # 2. CHECK STOP-LOSS (if enabled)
        # ========================================================
        if not self.sl_enabled:
            return to_close
        
        # Get list of positions already marked for closure (expiration)
        expired_position_ids = {item['position_id'] for item in to_close}
        
        for position_id, position in self.positions.items():
            # Skip positions already marked for closure (expired)
            if position_id in expired_position_ids:
                continue
            
            if position_id not in price_data:
                continue
            
            if isinstance(price_data[position_id], dict):
                data = price_data[position_id]
                current_price = data.get('price', position['entry_price'])
                current_pnl = data.get('pnl', 0)
                current_pnl_pct = data.get('pnl_pct')
                
                # ✅ If pnl_pct not provided, calculate correctly for CREDIT strategies
                if current_pnl_pct is None and position['entry_price'] == 0:
                    # CREDIT strategy - use MAX_RISK for percentage
                    # ⚠️ CRITICAL: entry_max_risk is ALREADY TOTAL (not per-contract!)
                    max_risk_total = position.get('entry_max_risk', 0)
                    
                    # If entry_max_risk not saved, calculate from strikes (Iron Condor)
                    if max_risk_total == 0:
                        # Try CALL strikes first
                        long_call = position.get('long_call_strike', 0)
                        short_call = position.get('short_call_strike', 0)
                        
                        # Fallback to PUT strikes if call strikes unavailable
                        long_put = position.get('long_put_strike', 0)
                        short_put = position.get('short_put_strike', 0)
                        
                        wing_width = 0
                        if long_call > 0 and short_call > 0:
                            wing_width = abs(long_call - short_call)
                        elif long_put > 0 and short_put > 0:
                            wing_width = abs(long_put - short_put)
                        
                        if wing_width > 0:
                            # ✅ Use abs() because total_cost is negative for credits
                            total_cost_per_contract = abs(position.get('total_cost', 0)) / position.get('contracts', 1)
                            max_risk_per_contract = (wing_width * 100) - total_cost_per_contract
                            contracts = position.get('contracts', 1)
                            max_risk_total = max_risk_per_contract * contracts
                    
                    if max_risk_total > 0:
                        current_pnl_pct = (current_pnl / max_risk_total) * 100
                    else:
                        current_pnl_pct = 0
                elif current_pnl_pct is None:
                    current_pnl_pct = 0
                
                # NEW: Pass underlying data for directional stop with intraday
                underlying_price = data.get('underlying_price')
                underlying_entry_price = data.get('underlying_entry_price')
                underlying_change_pct = data.get('underlying_change_pct')
                underlying_high = data.get('underlying_high')  # 🆕 For EOD H/L check
                underlying_low = data.get('underlying_low')    # 🆕 For EOD H/L check
                
                # 🔍 DEBUG: Check what we got from price_data
                debuginfo_level = self.config.get('debuginfo', 0)
                if debuginfo_level >= 2:
                    position_count = len([p for p in self.positions.values() if p.get('entry_date')])
                    if position_count <= 3:
                        print(f"  🔍 [CHECK_POSITIONS] {position_id}: data.underlying_entry_price={underlying_entry_price}, position.underlying_entry_price={position.get('underlying_entry_price', 'MISSING')}")
            else:
                current_price = price_data[position_id]
                current_pnl = (current_price - position['entry_price']) * position['quantity']
                current_pnl_pct = (current_price - position['entry_price']) / position['entry_price'] if position['entry_price'] != 0 else 0
                underlying_price = None
                underlying_entry_price = None
                underlying_change_pct = None
                underlying_high = None
                underlying_low = None
            
            position['highest_price'] = max(position['highest_price'], current_price)
            position['lowest_price'] = min(position['lowest_price'], current_price)
            
            if position['entry_price'] == 0:
                check_value = current_pnl_pct
            else:
                check_value = current_price
            
            # Pass all data to stop manager (including H/L for directional)
            final_uep = underlying_entry_price or position.get('entry_stock_price')
            
            stop_kwargs = {
                'pnl_pct': current_pnl_pct,
                'current_pnl': current_pnl,
                'total_cost': position.get('total_cost', 1),
                'underlying_price': underlying_price,
                'underlying_entry_price': final_uep,
                'underlying_change_pct': underlying_change_pct,
                'underlying_high': underlying_high,  # 🆕 For two-step check
                'underlying_low': underlying_low,    # 🆕 For two-step check
                'symbol': position.get('symbol')     # 🆕 For intraday API call
            }
            
            triggered, stop_level, stop_type, intraday_data = self.sl_manager.check_stop(
                position_id=position_id,
                current_price=check_value,
                current_date=current_date,
                position_type=position.get('strategy_type', 'LONG'),
                **stop_kwargs
            )
            
            # 🔍 DEBUG LEVEL 2: Log EVERY check for first 3 positions
            debuginfo_level = self.config.get('debuginfo', 0)
            if debuginfo_level >= 2:
                position_count = len([p for p in self.positions.values() if p.get('entry_date')])
                if position_count <= 3:
                    # Show profit target if available
                    target_pct = position.get('entry_profit_target', 0) * 100
                    
                    # Format values safely (handle None and combined stop dict)
                    check_str = f"{check_value:.2f}" if check_value is not None else "N/A"
                    
                    # ✅ Handle combined stop (stop_level is a dict)
                    if isinstance(stop_level, dict):
                        # Combined stop: show P&L threshold
                        pl_thresh = stop_level.get('pl_threshold', 0)
                        stop_str = f"{pl_thresh:.2f}"
                    elif stop_level is not None:
                        # Simple stop: show threshold as number
                        stop_str = f"{stop_level:.2f}"
                    else:
                        stop_str = "N/A"
                    
                    if target_pct > 0:
                        print(f"    🔍 {current_date}: P&L%={check_str}%, Target={target_pct:.0f}%, SL={stop_str}%, triggered={triggered}")
                    else:
                        print(f"    🔍 {current_date}: P&L%={check_str}%, SL={stop_str}%, triggered={triggered}")
            
            if triggered:
                stop_info = {
                    'position_id': position_id,
                    'symbol': position['symbol'], 
                    'stop_type': stop_type,
                    'current_price': current_price,
                    'pnl': current_pnl,
                    'pnl_pct': current_pnl_pct
                }
                
                # ✅ For combined stop: unpack dict instead of storing as nested object
                if stop_type == 'combined' and isinstance(stop_level, dict):
                    # Extract individual fields for CSV (not nested dict!)
                    stop_info['pl_threshold'] = stop_level.get('pl_threshold')
                    stop_info['dir_threshold'] = stop_level.get('dir_threshold')
                    stop_info['pl_condition'] = stop_level.get('pl_condition')
                    stop_info['dir_condition'] = stop_level.get('dir_condition')
                    stop_info['combined_logic'] = stop_level.get('logic')
                else:
                    # For other stops: store stop_level as scalar
                    stop_info['stop_level'] = stop_level
                
                # ✅ DETERMINE exit_reason based on stop type and conditions
                if stop_type == 'combined':
                    # For COMBINED STOP: Use trigger reason from unpacked fields
                    pl_condition = stop_info.get('pl_condition', False)
                    dir_condition = stop_info.get('dir_condition', False)
                    
                    # Determine reason based on which condition(s) triggered
                    if pl_condition and dir_condition:
                        exit_reason = 'stop_loss_combined_both'  # Both conditions (AND logic)
                    elif pl_condition:
                        exit_reason = 'stop_loss_combined_pl_loss'  # P&L loss triggered
                    elif dir_condition:
                        exit_reason = 'stop_loss_combined_directional'  # Directional triggered
                    else:
                        exit_reason = 'stop_loss_combined'  # Fallback
                    
                    stop_info['exit_reason'] = exit_reason
                elif stop_type == 'directional':
                    # For DIRECTIONAL: Add breach direction (high/low) from intraday_data
                    breach_dir = None
                    if intraday_data:
                        breach_dir = intraday_data.get('breach_direction')
                    if breach_dir:
                        stop_info['exit_reason'] = f"stop_loss_{stop_type}_{breach_dir}"
                    else:
                        stop_info['exit_reason'] = f"stop_loss_{stop_type}"
                else:
                    # For other stop types: generic reason
                    stop_info['exit_reason'] = f"stop_loss_{stop_type}"
                
                # ✅ ADD close_reason and stat_key for strategy stats
                stop_info['close_reason'] = stop_info['exit_reason']
                stop_info['stat_key'] = 'stoploss_triggered'
                
                # ✅ ADD stop-loss metadata for CSV export (stop_threshold, actual_value)
                # These fields are needed for detailed analysis of stop-loss triggers
                if stop_type == 'pl_loss':
                    # For P&L stop: threshold = -X%, actual = current P&L%
                    stop_info['stop_threshold'] = stop_level  # Already in % (e.g., -10.0)
                    stop_info['actual_value'] = current_pnl_pct
                elif stop_type == 'directional':
                    # For directional stop: threshold = X% move, actual = underlying change%
                    stop_info['stop_threshold'] = stop_level  # In % (e.g., 3.0)
                    stop_info['actual_value'] = underlying_change_pct
                elif stop_type == 'combined':
                    # For combined stop: use pl_threshold if available (already unpacked above)
                    stop_info['stop_threshold'] = stop_info.get('pl_threshold', stop_info.get('dir_threshold'))
                    stop_info['actual_value'] = current_pnl_pct
                else:
                    # For other stop types (trailing, fixed_pct, etc.)
                    stop_info['stop_threshold'] = stop_level
                    stop_info['actual_value'] = check_value
                
                # Add intraday data if available
                if intraday_data:
                    # ✅ _extract_intraday_fields() already returns renamed fields
                    # Just merge them into stop_info (no need for second mapping!)
                    stop_info.update(intraday_data)
                
                # ✅ AUTO-GENERATE close kwargs (so strategy code doesn't need to call generate_close_position_kwargs)
                strategy_type = position.get('strategy_type', 'STRADDLE')
                pos_data = price_data.get(position_id, {})
                close_kwargs = StrategyRegistry.generate_close_position_kwargs(strategy_type, pos_data)
                stop_info.update(close_kwargs)
                
                to_close.append(stop_info)
                
                if self.debug:
                    mode = "P&L%" if position['entry_price'] == 0 else "Price"
                    print(f"[PositionManager] 🔔 STOP-LOSS: {position_id} ({stop_type}, {mode}) @ {check_value:.2f}")
        
        return to_close
    
    def build_price_data(self, current_date, stock_price, options_df, get_option_func, 
                        indicators=None, extra_fields_callback=None):
        """
        Build price_data dict for all open positions.
        
        Args:
            current_date: Current backtest date
            stock_price: Current underlying price
            options_df: Options data for current date
            get_option_func: Function to get option by (strike, exp, type)
            indicators: Optional dict of indicators for current date
                       All fields will be added to price_data with 'exit_' prefix
                       (e.g., z_score → exit_z_score, iv_percentile → exit_iv_percentile)
            extra_fields_callback: Optional function(position, price_data) to add custom fields
                                  (e.g., directional stop fields, earnings data)
        
        Returns:
            Dict[position_id, price_data] for all open positions
        """
        price_data = {}
        
        for position in self.get_open_positions():
            # Get leg data from current market prices
            leg_data = StrategyRegistry.get_leg_data_for_position(
                position, options_df, get_option_func
            )
            
            if leg_data is not None:
                # Get strategy type
                strategy_type = position.get('strategy_type', self.config.get('strategy_type', 'STRADDLE'))
                
                # Auto-generate price_data (framework calculates P&L automatically!)
                price_data[position['id']] = StrategyRegistry.generate_price_data(
                    strategy_type=strategy_type,
                    leg_data=leg_data,
                    underlying_price=stock_price,
                    position=position
                )
                
                # Add ALL indicators with 'exit_' prefix (universal for any strategy)
                if indicators:
                    for indicator_name, indicator_value in indicators.items():
                        if indicator_value is not None:
                            # Add with exit_ prefix if not already prefixed
                            field_name = f'exit_{indicator_name}' if not indicator_name.startswith('exit_') else indicator_name
                            price_data[position['id']][field_name] = indicator_value
                
                # Add custom fields via callback (e.g., directional stop fields)
                if extra_fields_callback:
                    extra_fields = extra_fields_callback(position, price_data[position['id']])
                    if extra_fields:
                        price_data[position['id']].update(extra_fields)
        
        return price_data
    
    def close_remaining_positions(self, final_date, stock_price, options_df, get_option_func, 
                                  indicators=None):
        """
        Close all remaining open positions at end of backtest.
        
        Args:
            final_date: Final backtest date
            stock_price: Final underlying price
            options_df: Options data for final date
            get_option_func: Function to get option by (strike, exp, type)
            indicators: Optional dict of indicators for final date
        
        Returns:
            Total P&L from closing positions
        """
        if len(self.get_open_positions()) == 0:
            return 0
        
        if self.debug:
            print(f"\n⚠️  Closing {len(self.get_open_positions())} remaining open positions...")
        
        # Build price_data for all open positions
        price_data = self.build_price_data(
            final_date, stock_price, options_df, get_option_func, indicators
        )
        
        # Close all positions
        self.close_all_positions(final_date, price_data, 'end_of_backtest')
        
        # Calculate total P&L
        total_pnl = sum(data.get('pnl', 0) for data in price_data.values())
        
        if self.debug:
            print(f"  ✓ Closed {len(price_data)} positions at end of period")
        
        return total_pnl
    
    def close_position_by_signal(self, position_id, exit_date, price_data, close_reason='signal_exit'):
        """
        Close position manually by signal (z-score exit, earnings exit, etc.).
        
        This is a convenience method that handles all the boilerplate:
        - Gets position data from price_data
        - Generates close kwargs automatically
        - Closes the position
        - Returns pnl for capital update
        
        Args:
            position_id: ID of position to close
            exit_date: Current date
            price_data: Dict from build_price_data() or check_positions() context
            close_reason: Reason for closing (e.g., 'z_score_exit', 'earnings_exit')
        
        Returns:
            float: P&L of the closed position
            
        Example:
            if abs(z_score) <= config['z_score_exit']:
                pnl = position_mgr.close_position_by_signal(
                    position['id'], current_date, price_data, 'z_score_exit'
                )
                stats['signal_exits'] += 1
                capital += pnl
        """
        # Get position data
        pos_data = price_data.get(position_id, {})
        pnl = pos_data.get('pnl', 0)
        pnl_pct = pos_data.get('pnl_pct', 0)
        
        # Generate close kwargs automatically
        strategy_type = self.config.get('strategy_type', 'STRADDLE')
        kwargs = StrategyRegistry.generate_close_position_kwargs(strategy_type, pos_data)
        
        # Close position
        self.close_position(
            position_id=position_id,
            exit_date=exit_date,
            exit_price=0.0,
            close_reason=close_reason,
            pnl=pnl,
            pnl_pct=pnl_pct,
            stat_key='signal_exits',  # For consistency with other exits
            **kwargs
        )
        
        return pnl
    
    def check_profit_target(self, current_date, stock_price, options_df, get_option_func):
        """
        Check all positions for profit target achievement.
        
        Args:
            current_date: Current backtest date
            stock_price: Current underlying price
            options_df: DataFrame with filtered options for current date
            get_option_func: Function to get option data (strike, exp, type)
        
        Returns:
            list: List of dicts with position_id, pnl, pnl_pct for positions to close
            
        Example:
            positions_to_close = position_mgr.check_profit_target(
                current_date,
                stock_price,
                options_today,
                lambda s, e, t: get_option_by_strike_exp(options_today, s, e, t)
            )
            
            for target_info in positions_to_close:
                capital += target_info['pnl']
                position_mgr.close_position(
                    target_info['position_id'],
                    exit_date=current_date,
                    exit_price=0.0,
                    total_pnl=target_info['pnl'],
                    pnl_pct=target_info['pnl_pct'],
                    exit_reason='profit_target',
                    **target_info['kwargs']
                )
        """
        to_close = []
        
        for position_id, position in self.positions.items():
            # Get leg data using universal method
            leg_data = StrategyRegistry.get_leg_data_for_position(
                position,
                options_df,
                get_option_func
            )
            
            if not leg_data:
                if self.debug:
                    print(f"[check_profit_target] ⚠️  {position_id}: No option data found!")
                continue  # No option data available
            
            # Calculate P&L using framework
            strategy_type = position.get('strategy_type', 'UNKNOWN')
            pos_data = StrategyRegistry.generate_price_data(
                strategy_type,
                leg_data,
                underlying_price=stock_price,
                position=position,
                context='profit_target'  # ← For profit target: % of max profit
            )
            
            current_pnl = pos_data['pnl']
            pnl_pct = pos_data['pnl_pct']
            
            # Check profit target
            profit_target = position.get('entry_profit_target', 0.50)  # Default 50%
            target_pct = profit_target * 100
            
            if self.debug:
                print(f"[check_profit_target] 🔍 {position_id}: P&L={pnl_pct:.2f}%, Target={target_pct:.0f}%")
            
            # ✅ DETAILED DEBUG for debuginfo >= 2
            if self.debuginfo >= 2:
                entry_cost = position.get('total_cost', 0)
                max_risk = position.get('entry_max_risk', 0)
                credit_received = abs(entry_cost) if entry_cost < 0 else 0
                
                # Show old vs new calculation for comparison
                old_pnl_pct = (current_pnl / max_risk * 100) if max_risk > 0 else 0
                new_pnl_pct = (current_pnl / credit_received * 100) if credit_received > 0 else 0
                
                print(f"[check_profit_target] [DEBUG2] {position_id}:")
                print(f"   Entry Cost: ${entry_cost:.2f}, Max Risk: ${max_risk:.2f}, Credit: ${credit_received:.2f}")
                print(f"   Current P&L: ${current_pnl:.2f}")
                print(f"   📊 P&L% OLD (from max_risk): {old_pnl_pct:.2f}%")
                print(f"   📊 P&L% NEW (from credit):   {pnl_pct:.2f}% ← CORRECT!")
                print(f"   Profit Target: {target_pct:.0f}%, Achieved: {pnl_pct >= target_pct}")
                print(f"   Legs: {', '.join(leg_data.keys())}")
            
            if pnl_pct >= target_pct:
                # Generate kwargs for close_position
                kwargs = StrategyRegistry.generate_close_position_kwargs(strategy_type, pos_data)
                
                to_close.append({
                    'position_id': position_id,
                    'symbol': position['symbol'],
                    'close_reason': 'profit_target',  # ✅ For strategy stats
                    'stat_key': 'profit_target_exits',  # ✅ For strategy stats
                    'pnl': current_pnl,
                    'pnl_pct': pnl_pct,
                    'target_pct': target_pct,
                    'kwargs': kwargs
                })
                
                if self.debug:
                    print(f"[PositionManager] 💰 PROFIT TARGET: {position_id} @ {pnl_pct:.2f}% (target: {target_pct:.0f}%)")
        
        return to_close
    
    def close_position(self, position_id, exit_date, exit_price, 
                       close_reason='manual', pnl=None, pnl_pct=None,
                       portfolio_state_data=None, **kwargs):
        """
        Close position
        
        Args:
            portfolio_state_data (dict, optional): If provided and debuginfo >= 1, will print [PORTFOLIO STATE] logs.
                Required keys: 'current_capital', 'options_data', 'get_option_price_func'
        """
        if position_id not in self.positions:
            if self.debug:
                print(f"[PositionManager] WARNING: Position {position_id} not found")
            return None
        
        position = self.positions.pop(position_id)
        
        # Check if pnl provided in kwargs (takes priority over calculated)
        if pnl is None:
            pnl = kwargs.get('pnl', None)
        
        if pnl is None:
            pnl = (exit_price - position['entry_price']) * position['quantity']
        
        # ✅ NEW (v2.16.8): Use pnl_pct from parameter if provided (calculated by generate_price_data or check_positions)
        if pnl_pct is None:
            pnl_pct = kwargs.get('pnl_pct', None)
        
        if pnl_pct is None:
            # Calculate pnl_pct if not provided
            if position['entry_price'] != 0:
                pnl_pct = (exit_price - position['entry_price']) / position['entry_price'] * 100
            else:
                # Fallback for CREDIT strategies (entry_price = 0)
                # Use max_risk as denominator (more accurate than credit received)
                # ⚠️ CRITICAL: entry_max_risk is ALREADY TOTAL (not per-contract!)
                max_risk_total = position.get('entry_max_risk', 0)
                
                if max_risk_total > 0:
                    # ✅ Use max_risk for accurate P&L%
                    pnl_pct = (pnl / max_risk_total) * 100
                else:
                    # Emergency fallback: if max_risk not found
                    total_cost = position.get('total_cost', kwargs.get('total_cost', 0))
                    is_credit = total_cost < 0
                    
                    if is_credit:
                        # CREDIT: Try to use max_risk from position, or use abs(total_cost) as last resort
                        max_risk = position.get('max_risk', abs(total_cost))
                        pnl_pct = (pnl / max_risk) * 100 if max_risk > 0 else 0.0
                    else:
                        # DEBIT: Use total_cost (premium paid)
                        pnl_pct = (pnl / abs(total_cost)) * 100 if total_cost != 0 else 0.0        
                
        trade = {
            'entry_date': position['entry_date'],
            'exit_date': exit_date,
            'symbol': position['symbol'],
            'signal': position.get('strategy_type', ''),
            'strategy_type': position.get('strategy_type', ''),  # Strategy type for CSV
            'entry_price': position['entry_price'],
            'exit_price': exit_price,
            'quantity': position['quantity'],
            'pnl': pnl,
            'return_pct': pnl_pct,
            'pnl_pct': pnl_pct,  # ✅ CRITICAL: Export 'pnl_pct' (same as return_pct for compatibility)
            'exit_reason': close_reason,
            'stop_type': self.sl_config.get('type', 'none') if self.sl_enabled else 'none',
            **kwargs
        }
        
        for key in ['strike',  # Universal strike (for straddles - same strike for call/put)
                    'call_strike', 'put_strike',  # Separate strikes (for strangles)
                    'expiration',  # Universal expiration (for straddles/strangles - same date for call/put)
                    'call_expiration', 'put_expiration',  # Separate expirations (for strangles with different dates)
                    'contracts', 
                    'short_strike', 'long_strike',  # For spreads (iron condor, butterfly, etc.)
                    'short_expiration', 'long_expiration',  # For calendar spreads (different expirations)
                    'opt_type', 'spread_type',
                    # ✅ CRITICAL: Iron Condor strikes (4 legs)
                    'short_call_strike', 'long_call_strike', 'short_put_strike', 'long_put_strike',
                    # ✅ CRITICAL: Position metadata
                    'dte', 'position_size_pct', 'total_cost', 'strategy_type',
                    # ✅ CRITICAL: Risk data for validation
                    'entry_max_risk', 'max_risk', 'capital_at_risk',
                    'capital_at_entry', 'target_allocation', 'actual_allocation',
                    'available_equity_at_entry', 'locked_capital_at_entry', 'open_positions_at_entry',
                    'highest_price', 'lowest_price',
                    # IV Lean specific
                    'entry_z_score', 'entry_lean', 'exit_lean', 'iv_lean_entry',
                    # IV data
                    'call_iv_entry', 'put_iv_entry', 'iv_entry',
                    'iv_rank_entry', 'iv_percentile_entry',
                    # Iron Condor IV at entry (4 separate legs)
                    'short_call_iv_entry', 'long_call_iv_entry', 'short_put_iv_entry', 'long_put_iv_entry',
                    # Greeks at entry (✅ EXPORTED AT ENTRY!)
                    'call_vega_entry', 'call_theta_entry', 'put_vega_entry', 'put_theta_entry',
                    'call_delta_entry', 'call_gamma_entry', 'put_delta_entry', 'put_gamma_entry',
                    'net_delta_entry', 'net_gamma_entry', 'net_vega_entry', 'net_theta_entry',
                    # Iron Condor Greeks at entry (4 separate legs)
                    'short_call_delta_entry', 'short_call_gamma_entry', 'short_call_vega_entry', 'short_call_theta_entry',
                    'long_call_delta_entry', 'long_call_gamma_entry', 'long_call_vega_entry', 'long_call_theta_entry',
                    'short_put_delta_entry', 'short_put_gamma_entry', 'short_put_vega_entry', 'short_put_theta_entry',
                    'long_put_delta_entry', 'long_put_gamma_entry', 'long_put_vega_entry', 'long_put_theta_entry',
                    # Entry criteria (universal for all strategies)
                    'target_delta_entry', 'delta_threshold_entry',
                    'entry_price_pct', 'distance_from_strike_entry',
                    'dte_entry', 'target_dte_entry',
                    'volume_entry', 'open_interest_entry', 'volume_ratio_entry',
                    'entry_criteria', 'entry_signal', 'entry_reason',
                    # High Vega specific entry data
                    'entry_iv_rank', 'entry_signal_type', 'entry_wing_width', 'entry_vega_per_contract']:
            if key in position:
                trade[key] = position[key]
        
        for key in ['short_entry_bid', 'short_entry_ask', 'short_entry_mid',
                    'long_entry_bid', 'long_entry_ask', 'long_entry_mid',
                    # Call/Put entry prices (for straddle/strangle strategies)
                    'call_entry_bid', 'call_entry_ask', 'call_entry_mid',
                    'put_entry_bid', 'put_entry_ask', 'put_entry_mid',
                    # Iron Condor entry prices (4 separate legs)
                    'short_call_entry_bid', 'short_call_entry_ask', 'short_call_entry_mid',
                    'long_call_entry_bid', 'long_call_entry_ask', 'long_call_entry_mid',
                    'short_put_entry_bid', 'short_put_entry_ask', 'short_put_entry_mid',
                    'long_put_entry_bid', 'long_put_entry_ask', 'long_put_entry_mid',
                    'underlying_entry_price']:
            if key in position:
                trade[key] = position[key]
        
        for key in ['short_exit_bid', 'short_exit_ask',
                    'long_exit_bid', 'long_exit_ask',
                    # Call/Put exit prices (for straddle/strangle strategies)
                    'call_exit_bid', 'call_exit_ask', 'put_exit_bid', 'put_exit_ask',
                    # Iron Condor exit prices (4 separate legs)
                    'short_call_exit_bid', 'short_call_exit_ask',
                    'long_call_exit_bid', 'long_call_exit_ask',
                    'short_put_exit_bid', 'short_put_exit_ask',
                    'long_put_exit_bid', 'long_put_exit_ask',
                    'underlying_exit_price', 'underlying_change_pct',
                    'stop_threshold', 'actual_value',
                    # IV data at exit
                    'call_iv_exit', 'put_iv_exit', 'iv_lean_exit', 'iv_exit',
                    'iv_rank_exit', 'iv_percentile_exit',
                    # Iron Condor IV at exit (4 separate legs)
                    'short_call_iv_exit', 'long_call_iv_exit', 'short_put_iv_exit', 'long_put_iv_exit',
                    # IV Lean Z-score at exit (for IV Lean strategies)
                    'exit_z_score',
                    # Greeks at exit (✅ EXPORTED AT EXIT!)
                    'call_vega_exit', 'call_theta_exit', 'put_vega_exit', 'put_theta_exit',
                    'call_delta_exit', 'call_gamma_exit', 'put_delta_exit', 'put_gamma_exit',
                    'net_delta_exit', 'net_gamma_exit', 'net_vega_exit', 'net_theta_exit',
                    # Iron Condor Greeks at exit (4 separate legs)
                    'short_call_delta_exit', 'short_call_gamma_exit', 'short_call_vega_exit', 'short_call_theta_exit',
                    'long_call_delta_exit', 'long_call_gamma_exit', 'long_call_vega_exit', 'long_call_theta_exit',
                    'short_put_delta_exit', 'short_put_gamma_exit', 'short_put_vega_exit', 'short_put_theta_exit',
                    'long_put_delta_exit', 'long_put_gamma_exit', 'long_put_vega_exit', 'long_put_theta_exit',
                    # Exit criteria (universal for all strategies)
                    'target_delta_exit', 'delta_threshold_exit',
                    'exit_price_pct', 'distance_from_strike_exit',
                    'dte_exit', 'target_dte_exit',
                    'volume_exit', 'open_interest_exit', 'volume_ratio_exit',
                    'exit_criteria', 'exit_signal', 'exit_reason',
                    # Intraday fields (universal - works for any underlying symbol)
                    'stock_intraday_high', 'stock_intraday_low', 'stock_intraday_close',
                    'stock_stop_trigger_time', 'stock_stop_trigger_price',
                    'stock_stop_trigger_bid', 'stock_stop_trigger_ask', 'stock_stop_trigger_last',
                    'intraday_data_points', 'intraday_data_available', 'stop_triggered_by',
                    # 🆕 Directional stop breach details
                    'breach_direction', 'stop_level_high', 'stop_level_low',
                    'intraday_bar_index', 'intraday_volume',
                    'intraday_trigger_bid_time', 'intraday_trigger_ask_time']:
            if key in kwargs:
                trade[key] = kwargs[key]
        
        # ========================================================
        # AUTO-COPY LEG DATA (spreads with multiple legs)
        # ========================================================
        # For multi-leg spreads: long_call_*, short_call_*, long_put_*, short_put_*
        # Copies all entry/exit/greeks/iv fields automatically for legs
        for key in list(position.keys()) + list(kwargs.keys()):
            # Entry leg data from position (e.g., long_call_entry_bid, short_put_delta_entry, etc.)
            if any(key.startswith(prefix) for prefix in [
                'long_call_', 'short_call_', 'long_put_', 'short_put_',
                'long_', 'short_', 'call_', 'put_'
            ]):
                if '_entry_' in key or '_delta_entry' in key or '_gamma_entry' in key or \
                   '_vega_entry' in key or '_theta_entry' in key or '_iv_entry' in key or \
                   '_strike' in key or '_expiration' in key:
                    if key in position and key not in trade:
                        trade[key] = position[key]
        
        # ========================================================
        # AUTO-COPY ALL CUSTOM ENTRY FIELDS
        # ========================================================
        # Universal mechanism: copy ANY field starting with 'entry_' from position to trade
        # This allows strategies to add custom fields without modifying the framework
        for key in position.keys():
            if key.startswith('entry_') and key not in trade:
                        trade[key] = position[key]
        
        self.closed_trades.append(trade)
        
        if self.sl_enabled and self.sl_manager:
            self.sl_manager.remove_position(position_id)
        
        # ========================================================
        # FORWARD-FILL CLEANUP: Remove cached prices for closed position
        # ========================================================
        if position_id in self.last_known_price_data:
            del self.last_known_price_data[position_id]
        
        # Update cumulative P&L (always, not just when debug)
        self.cumulative_pnl += pnl
        
        if self.debug:
            cumulative_pnl_pct = (self.cumulative_pnl / self.initial_capital) * 100
            
            # Color-coded output with emoji
            if pnl >= 0:
                emoji = "✅"
                color_start = "\033[92m"  # Bright green
                color_end = "\033[0m"     # Reset
            else:
                emoji = "❌"
                color_start = "\033[38;2;239;124;94m"  # Coral-red #EF7C5E
                color_end = "\033[0m"     # Reset
            
            # Color for cumulative P&L
            if self.cumulative_pnl >= 0:
                cum_color = "\033[92m"  # Green
            else:
                cum_color = "\033[38;2;239;124;94m"  # Coral-red #EF7C5E
            
            print(f"[PositionManager] {color_start}{emoji} CLOSE {position_id}: P&L=${pnl:.2f} ({pnl_pct:.2f}%) - {close_reason}{color_end}")
            print(f"               \033[90m   📊 CUMULATIVE P&L:\033[0m {cum_color}\033[1m\033[4m${self.cumulative_pnl:.2f} ({cumulative_pnl_pct:+.2f}%)\033[0m")
        
        # ========================================================
        # PORTFOLIO STATE AFTER POSITION CLOSE (HYBRID APPROACH)
        # ========================================================
        if portfolio_state_data and self.debug:
            try:
                capital_info = self.calculate_available_capital(
                    current_capital=portfolio_state_data['current_capital'],
                    options_data=portfolio_state_data['options_data'],
                    get_option_price_func=portfolio_state_data['get_option_price_func']
                )
                
                print(f"\033[90m[PORTFOLIO STATE] {exit_date}\033[0m")
                print(f"\033[90m  Total capital: ${capital_info['total_capital']:,.2f}\033[0m")
                print(f"\033[90m  Open positions: {capital_info['open_positions_count']}\033[0m")
                print(f"\033[90m  Capital at risk: ${capital_info['capital_at_risk']:,.2f}\033[0m")
                print(f"\033[90m  Available equity: ${capital_info['available_capital']:,.2f}\033[0m")
            except Exception as e:
                if self.debug:
                    print(f"[PositionManager] WARNING: Failed to print portfolio state: {e}")
        
        return trade
            
    def get_open_positions(self):
        return list(self.positions.values())
    
    def get_closed_trades(self):
        return self.closed_trades
    
    def _fetch_current_leg_prices(self, position, get_option_price_func):
        """
        Fetch current market prices for all legs of a multi-leg strategy.
        
        Args:
            position (dict): Position data with leg strike information
            get_option_price_func (callable): Function to get option prices
                                             signature: (strike, expiration, opt_type) -> option_data
        
        Returns:
            dict: {leg_name: option_data, ...} for all strategy legs
            
        Raises:
            ValueError: If required position fields are missing
            KeyError: If option prices cannot be fetched
        """
        position_type = position.get('strategy_type', 'STRADDLE')
        strategy = StrategyRegistry.get(position_type)
        
        if not strategy:
            raise ValueError(f"Strategy {position_type} not registered")
        
        legs = strategy.get('legs', [])
        if not legs:
            raise ValueError(f"Strategy {position_type} has no legs defined")
        
        leg_data = {}
        expiration = position.get('expiration')
        
        for leg in legs:
            leg_name = leg['name']
            
            # Map leg name to strike field (e.g., 'short_call' -> 'short_call_strike')
            # Convention: leg names map to '{leg_name}_strike' fields
            strike_field = f"{leg_name}_strike"
            strike = position.get(strike_field)
            
            if strike is None:
                raise KeyError(f"Position missing field: {strike_field}")
            
            # Determine option type from leg name
            opt_type = 'C' if 'call' in leg_name.lower() else 'P'
            
            # Fetch current option price
            option = get_option_price_func(strike, expiration, opt_type)
            
            if option is None:
                raise KeyError(f"Cannot fetch option price: strike={strike}, exp={expiration}, type={opt_type}")
            
            leg_data[leg_name] = option
        
        return leg_data
    
    def calculate_available_capital(self, current_capital, options_data, get_option_price_func):
        """
        Calculate available capital for new positions (Dynamic Equity Allocation)
        
        ✨ NEW: Uses MARKET-BASED approach for capital at risk calculation.
        - Primary: Calculate current close cost using real market prices (accurate)
        - Fallback: Use theoretical max loss calculation (conservative)
        
        Args:
            current_capital (float): Current total capital
            options_data (dict): Current options data for pricing
            get_option_price_func (callable): Function to get option prices
                                             signature: (strike, expiration, opt_type) -> option_data
        
        Returns:
            dict: {
                'total_capital': float,
                'locked_capital': float,      # Premium collected from open positions
                'unrealized_pnl': float,      # Current unrealized P&L
                'capital_at_risk': float,     # Estimated maximum loss exposure
                'available_capital': float,   # Capital available for new trades
                'open_positions_count': int
            }
        """
        locked_capital = 0
        unrealized_pnl = 0
        capital_at_risk = 0
        
        for position in self.get_open_positions():
            # Use StrategyRegistry for standardized risk calculation
            position_type = position.get('strategy_type', 'STRADDLE')
            
            # Try registry first (data-driven from STRATEGIES)
            strategy = StrategyRegistry.get(position_type)
            if strategy:
                # ========================================
                # MARKET-BASED APPROACH (PRIMARY)
                # ========================================
                # Try to calculate capital at risk using CURRENT market prices
                # This is more accurate than theoretical calculation
                try:
                    # Fetch current prices for all legs
                    leg_data = self._fetch_current_leg_prices(position, get_option_price_func)
                    
                    # Calculate current cost to close using real market prices
                    current_close_cost = StrategyRegistry.calculate_close_cost(
                        position_type, position, leg_data
                    )
                    
                    # Calculate unrealized P&L
                    entry_cost = position.get('total_cost', 0)
                    
                    # ✅ Universal CREDIT detection (works for ANY strategy)
                    is_credit = StrategyRegistry.is_credit_strategy(
                        strategy_type=position_type, position=position
                    )
                    
                    if is_credit:
                        # CREDIT: pnl = credit_received - buyback_cost
                        unrealized_pnl += (entry_cost - current_close_cost)
                    else:
                        # DEBIT: pnl = sell_proceeds - debit_paid
                        unrealized_pnl += (current_close_cost - entry_cost)
                    
                    # ========================================
                    # SAFETY BUFFER: 1.5x multiplier (50% buffer)
                    # ========================================
                    # WHY 1.5x for EOD (end-of-day) backtests:
                    #
                    # 1. SLIPPAGE PROTECTION (+10-20%)
                    #    - Bid/ask spread may be worse than historical data
                    #    - Market impact on larger positions
                    #
                    # 2. GAP RISK (+10-30%)
                    #    - Overnight gaps between close and next open
                    #    - Critical for EOD data (no intraday control)
                    #    - Can't exit during gap events
                    #
                    # 3. VOLATILITY SPIKE BUFFER (+10-20%)
                    #    - IV can spike suddenly (VIX events)
                    #    - Option prices explode during fear
                    #
                    # 4. CONSERVATIVE ESTIMATION
                    #    - Better to overestimate risk than underestimate
                    #    - Prevents over-allocation of capital
                    #
                    # REAL WORLD COMPARISON:
                    # - Broker margin requirements: 1.0x (just max loss)
                    # - TastyTrade/OptionAlpha: 1.0x (buying power reduction)
                    # - Conservative backtests: 1.5x-2.0x (accounts for slippage)
                    # - Academic papers: varies 1.0x-2.0x
                    #
                    # ALTERNATIVES by data type:
                    # - EOD data: 1.5x (current) - conservative, realistic
                    # - Intraday data: 1.2x-1.3x - less buffer needed
                    # - Live simulation: 1.0x-1.1x - closest to reality
                    #
                    # NOTE: This is MORE conservative than real broker requirements
                    # but appropriate for EOD backtesting with limited execution control
                    # ========================================
                    capital_at_risk += abs(current_close_cost) * 1.5
                    locked_capital += abs(entry_cost)
                    
                    if self.debug:
                        print(f"[PositionManager] Market-based risk for {position_type}: "
                              f"close_cost=${current_close_cost:.2f}, "
                              f"risk=${abs(current_close_cost) * 1.5:.2f}")
                    
                    continue
                    
                except (ValueError, KeyError) as e:
                    # Fallback to theoretical calculation if market prices unavailable
                    if self.debug:
                        print(f"[PositionManager] Market-based calculation failed for {position_type}: {e}")
                        print(f"[PositionManager] Falling back to theoretical calculation")
                
                # ========================================
                # THEORETICAL APPROACH (FALLBACK)
                # ========================================
                # Use stored position data and theoretical max loss
                # This is used when current market prices are unavailable
                # (e.g., weekends, holidays, missing data)
                #
                # NOTE: StrategyRegistry.calculate_risk() uses SAME 1.5x buffer
                # as defined in risk_formula for each strategy in STRATEGIES dict
                # Example: 'IRON_CONDOR' → 'max((wing_width * 100 - credit) * 1.5, credit * 2)'
                #
                # This ensures consistency: whether market-based or theoretical,
                # the 1.5x safety buffer is ALWAYS applied
                # ========================================
                risk, locked = StrategyRegistry.calculate_risk(position)
                capital_at_risk += risk
                locked_capital += locked
                continue
            
            # ========================================
            # FALLBACK: Legacy calculation for non-registered strategies
            # ========================================
            if position_type == 'IRON_CONDOR':
                # Iron Condor: short call spread + short put spread
                # Max loss = wing_width * 100 * contracts - credit
                wing_width = position.get('wing_width', 5)
                contracts = position.get('contracts', 1)
                credit = position.get('total_cost', 0)
                
                # Max loss per spread = (wing_width * 100) - credit_per_contract
                max_loss_per_contract = (wing_width * 100) - (credit / contracts if contracts > 0 else 0)
                max_loss = max_loss_per_contract * contracts
                
                # Capital at risk = max loss + safety buffer
                capital_at_risk += max(max_loss * 1.5, credit * 2)
                locked_capital += credit
            
            # ========================================
            # VERTICAL SPREADS (2-leg: credit or debit)
            # ========================================
            elif position_type in ['BULL_CALL_SPREAD', 'BEAR_PUT_SPREAD', 
                                   'BULL_PUT_SPREAD', 'BEAR_CALL_SPREAD',
                                   'CREDIT_SPREAD', 'DEBIT_SPREAD']:
                contracts = position.get('contracts', 1)
                total_cost = position.get('total_cost', 0)
                
                # Calculate spread width
                short_strike = position.get('short_strike', 0)
                long_strike = position.get('long_strike', 0)
                
                if short_strike and long_strike:
                    spread_width = abs(long_strike - short_strike)
                    
                    # Credit spreads: max loss = (spread_width * 100 * contracts) - credit
                    # Debit spreads: max loss = debit paid (already in total_cost)
                    if position_type in ['BULL_PUT_SPREAD', 'BEAR_CALL_SPREAD', 'CREDIT_SPREAD']:
                        # Credit spread: we received premium, max loss is spread width minus credit
                        max_loss = (spread_width * 100 * contracts) - total_cost
                    else:
                        # Debit spread: we paid premium, max loss is what we paid
                        max_loss = total_cost
                    
                    capital_at_risk += max(abs(max_loss) * 1.5, abs(total_cost) * 2)
                    locked_capital += abs(total_cost)
                else:
                    # Fallback if strikes not found
                    capital_at_risk += abs(total_cost) * 2
                    locked_capital += abs(total_cost)
            
            # ========================================
            # BUTTERFLY (3-leg or 4-leg symmetrical)
            # ========================================
            elif position_type in ['BUTTERFLY', 'IRON_BUTTERFLY']:
                contracts = position.get('contracts', 1)
                total_cost = position.get('total_cost', 0)
                
                # For long butterfly: max loss = net debit paid
                # For iron butterfly: max loss = width of wings - credit
                wing_width = position.get('wing_width', 10)
                
                if position_type == 'IRON_BUTTERFLY':
                    # Iron butterfly: short straddle + protective wings
                    # Max loss = (wing_width * 100 * contracts) - credit
                    max_loss = (wing_width * 100 * contracts) - total_cost
                    capital_at_risk += max(abs(max_loss) * 1.5, abs(total_cost) * 2)
                else:
                    # Regular butterfly: max loss = net debit
                    capital_at_risk += abs(total_cost) * 1.5
                
                locked_capital += abs(total_cost)
            
            # ========================================
            # CONDOR (4-leg wider butterfly)
            # ========================================
            elif position_type == 'CONDOR':
                contracts = position.get('contracts', 1)
                total_cost = position.get('total_cost', 0)
                wing_width = position.get('wing_width', 10)
                
                # Similar to butterfly but wider body
                # Max loss = net debit paid (for long condor)
                capital_at_risk += abs(total_cost) * 1.5
                locked_capital += abs(total_cost)
            
            # ========================================
            # CALENDAR/DIAGONAL SPREADS (different expirations)
            # ========================================
            elif position_type in ['CALENDAR_SPREAD', 'DIAGONAL_SPREAD']:
                contracts = position.get('contracts', 1)
                total_cost = position.get('total_cost', 0)
                
                # Max loss = net debit paid (front month + back month)
                # Conservative: assume total cost could be lost
                capital_at_risk += abs(total_cost) * 2
                locked_capital += abs(total_cost)
            
            # ========================================
            # COVERED CALL (stock + short call)
            # ========================================
            elif position_type == 'COVERED_CALL':
                contracts = position.get('contracts', 1)
                underlying_price = position.get('underlying_entry_price', 0)
                
                # ✅ Use call_premium if available, fallback to total_cost for backward compatibility
                # Ideally: call_premium should be stored separately, but total_cost works as fallback
                call_premium = position.get('call_premium', abs(position.get('total_cost', 0)))
                
                # Capital at risk = stock value (we own stock)
                # Call premium reduces risk slightly
                stock_value = underlying_price * contracts * 100
                capital_at_risk += max(stock_value - call_premium, stock_value * 0.8)
                locked_capital += stock_value
            
            # ========================================
            # CASH-SECURED PUT (short put with cash reserve)
            # ========================================
            elif position_type == 'CASH_SECURED_PUT':
                contracts = position.get('contracts', 1)
                strike = position.get('strike', 0)
                credit = position.get('total_cost', 0)  # Premium received
                
                # Capital at risk = strike * 100 * contracts (cash secured)
                # We collected premium, so max loss is strike - premium
                cash_secured = strike * 100 * contracts
                max_loss = cash_secured - credit
                capital_at_risk += max_loss
                locked_capital += cash_secured
            
            # ========================================
            # RATIO SPREAD (unbalanced legs, e.g., 1x2, 1x3)
            # ========================================
            elif position_type in ['CALL_RATIO_SPREAD', 'PUT_RATIO_SPREAD']:
                contracts = position.get('contracts', 1)
                total_cost = position.get('total_cost', 0)
                
                # Conservative: ratio spreads have unlimited risk if wrong direction
                # Use 3x multiplier for safety
                capital_at_risk += abs(total_cost) * 3
                locked_capital += abs(total_cost)
            
            # ========================================
            # STRADDLE/STRANGLE (ATM or OTM call + put)
            # ========================================
            elif position_type in ['STRADDLE', 'STRANGLE', 'SELL_STRADDLE', 'SELL_STRANGLE',
                                   'BUY_STRADDLE', 'BUY_STRANGLE']:
                # Original logic for STRADDLE/STRANGLE with single strike
                if 'strike' not in position:
                    # Fallback: use conservative estimate
                    capital_at_risk += position.get('total_cost', 0) * 2
                    locked_capital += position.get('total_cost', 0)
                    continue
                    
                call_current = get_option_price_func(
                    position['strike'], 
                    position['expiration'], 
                    'C'
                )
                put_current = get_option_price_func(
                    position['strike'], 
                    position['expiration'], 
                    'P'
                )
                
                if call_current is not None and put_current is not None:
                    # Current cost to close (what we'd pay to buy back)
                    current_cost = (call_current['ask'] + put_current['ask']) * position['contracts'] * 100
                    
                    # Premium collected (baseline)
                    locked_capital += position['total_cost']
                    
                    # Unrealized P&L = premium collected - current cost
                    unrealized_pnl += (position['total_cost'] - current_cost)
                    
                    # Capital at risk = CURRENT cost × 1.5 (50% safety buffer)
                    capital_at_risk += current_cost * 1.5
                else:
                    # If options not found, use conservative estimate
                    capital_at_risk += position.get('total_cost', 0) * 2
            
            # ========================================
            # SINGLE LEG (naked call/put, protective put/call)
            # ========================================
            elif position_type in ['LONG_CALL', 'LONG_PUT', 'SHORT_CALL', 'SHORT_PUT',
                                   'PROTECTIVE_PUT', 'PROTECTIVE_CALL']:
                contracts = position.get('contracts', 1)
                total_cost = position.get('total_cost', 0)
                
                # For long options: max loss = premium paid
                # For short options: theoretically unlimited, use conservative estimate
                if position_type in ['LONG_CALL', 'LONG_PUT', 'PROTECTIVE_PUT', 'PROTECTIVE_CALL']:
                    capital_at_risk += abs(total_cost) * 1.2
                else:
                    # Short naked options: high risk, use 5x multiplier
                    capital_at_risk += abs(total_cost) * 5
                
                locked_capital += abs(total_cost)
            
            # ========================================
            # FALLBACK (unknown or custom strategies)
            # ========================================
            else:
                # Conservative fallback for any unknown strategy type
                total_cost = position.get('total_cost', 0)
                capital_at_risk += abs(total_cost) * 2
                locked_capital += abs(total_cost)
        
        # Available capital = total - capital at risk
        available_capital = max(0, current_capital - capital_at_risk)
        
        return {
            'total_capital': current_capital,
            'locked_capital': locked_capital,
            'unrealized_pnl': unrealized_pnl,
            'capital_at_risk': capital_at_risk,
            'available_capital': available_capital,
            'open_positions_count': len(self.positions)
        }
    
    def calculate_position_size(self, current_capital, position_size_pct, 
                               cost_per_contract, options_data, get_option_price_func,
                               min_contracts=1, debug=False, current_date=None, entry_context=None):
        """
        Calculate optimal position size using Dynamic Equity Allocation
        
        This method manages risk by considering capital already at risk from open positions.
        It calculates how much capital is available for new trades and sizes positions accordingly.
        
        Args:
            current_capital (float): Current total capital
            position_size_pct (float): Target allocation % (e.g., 0.30 for 30%)
            cost_per_contract (float): Cost of 1 contract (premium for straddle)
            options_data (dict): Current options data for pricing
            get_option_price_func (callable): Function to get option prices
                                             signature: (strike, expiration, opt_type) -> option_data
            min_contracts (int): Minimum contracts (default: 1)
            debug (bool): Print debug info (default: False)
            current_date: Current date for debug logs (optional)
            entry_context (dict): Additional context for debug logs (optional)
                                 e.g., {'z_score': -2.03, 'call_bid': 11.50, 'put_bid': 10.90}
        
        Returns:
            dict: {
                'num_contracts': int,          # Number of contracts to trade
                'target_allocation': float,    # Target position size ($)
                'actual_allocation': float,    # Actual position size ($)
                'total_capital': float,
                'available_capital': float,
                'capital_at_risk': float,
                'locked_capital': float,
                'unrealized_pnl': float,
                'open_positions_count': int,
                'allocation_pct_of_total': float,     # % of total capital
                'allocation_pct_of_available': float  # % of available capital
            }
        
        Example usage:
            # In your strategy, when you find an entry signal:
            cost_per_straddle = (call_bid + put_bid) * 100
            
            # Simple usage (no debug)
            sizing_info = position_mgr.calculate_position_size(
                current_capital=capital,
                position_size_pct=0.30,
                cost_per_contract=cost_per_straddle,
                options_data=options_today,
                get_option_price_func=lambda s, e, t: get_option_by_strike_exp(options_today, s, e, t)
            )
            
            # With debug logs (automatic [ENTRY SIGNAL] or [ENTRY BLOCKED] output)
            sizing_info = position_mgr.calculate_position_size(
                current_capital=capital,
                position_size_pct=0.30,
                cost_per_contract=cost_per_straddle,
                options_data=options_today,
                get_option_price_func=lambda s, e, t: get_option_by_strike_exp(options_today, s, e, t),
                debug=config.get('debuginfo', 0) >= 1,
                current_date=current_date,
                entry_context={'z_score': z_score, 'call_bid': call_bid, 'put_bid': put_bid}
            )
            
            # Check if we have available capital
            if sizing_info['available_capital'] <= 0:
                continue
            
            # Use the calculated number of contracts
            num_contracts = sizing_info['num_contracts']
        """
        # Get available capital info
        capital_info = self.calculate_available_capital(
            current_capital, 
            options_data, 
            get_option_price_func
        )
        
        available_capital = capital_info['available_capital']
        
        # Calculate target allocation (% of available capital)
        target_allocation = available_capital * position_size_pct
        
        # Calculate number of contracts (round down, minimum min_contracts)
        num_contracts = max(min_contracts, int(target_allocation / cost_per_contract))
        
        # Actual allocation
        actual_allocation = cost_per_contract * num_contracts
        
        # Calculate percentages
        allocation_pct_of_total = (actual_allocation / current_capital * 100) if current_capital > 0 else 0
        allocation_pct_of_available = (actual_allocation / available_capital * 100) if available_capital > 0 else 0
        
        # Debug output (multiline format)
        if debug:
            date_str = f" {current_date}" if current_date else ""
            
            if available_capital <= 0:
                print(f"\033[90m[ENTRY BLOCKED]{date_str}\033[0m")
                print(f"\033[90m  Total capital: ${capital_info['total_capital']:,.2f}\033[0m")
                print(f"\033[90m  Open positions: {capital_info['open_positions_count']}\033[0m")
                print(f"\033[90m  Capital at risk: ${capital_info['capital_at_risk']:,.2f}\033[0m")
                print(f"\033[90m  Available equity: ${capital_info['available_capital']:,.2f}\033[0m")
            else:
                print(f"\033[90m[ENTRY SIGNAL]{date_str}\033[0m")
                print(f"\033[90m  Total capital: ${capital_info['total_capital']:,.2f}\033[0m")
                print(f"\033[90m  Open positions: {capital_info['open_positions_count']}\033[0m")
                print(f"\033[90m  Capital at risk: ${capital_info['capital_at_risk']:,.2f}\033[0m")
                print(f"\033[90m  Available equity: ${capital_info['available_capital']:,.2f}\033[0m")
                print(f"\033[90m  Cost per contract: ${cost_per_contract:,.2f}\033[0m")
                print(f"\033[90m    (For DEBIT: premium paid | For CREDIT: max risk)\033[0m")
                print(f"\033[90m  Target allocation ({position_size_pct*100:.0f}%): ${target_allocation:,.2f}\033[0m")
                print(f"\033[90m  Contracts to trade: {num_contracts}\033[0m")
                
                # Additional context if provided
                if entry_context:
                    strategy_type = entry_context.get('strategy_type', '')
                    
                    # Use StrategyRegistry for formatted output (data-driven from STRATEGIES)
                    if strategy_type and StrategyRegistry.get(strategy_type):
                        debug_lines = StrategyRegistry.format_debug_output(strategy_type, entry_context)
                        for line in debug_lines:
                            print(f"\033[90m{line}\033[0m")
                        
                        # Universal fields (not strategy-specific)
                        if 'z_score' in entry_context and entry_context['z_score'] is not None:
                            print(f"\033[90m  Z-score: {entry_context['z_score']:.2f}\033[0m")
                    
                    # Legacy fallback for non-registered strategies
                    elif strategy_type == 'IRON_CONDOR':
                        print(f"\033[90m  ─────────────────────────────────────────\033[0m")
                        print(f"\033[90m  Strategy: IRON CONDOR\033[0m")
                        print(f"\033[90m  Wing Width: ${entry_context.get('wing_width', 0):.0f}\033[0m")
                        print(f"\033[90m  Call Delta: {entry_context.get('call_delta', 0):.3f} | Put Delta: {entry_context.get('put_delta', 0):.3f}\033[0m")
                        print(f"\033[90m  Total Credit: ${entry_context.get('total_credit', 0):.2f}\033[0m")
                        print(f"\033[90m    • Call Spread: ${entry_context.get('call_spread_credit', 0):.2f}\033[0m")
                        print(f"\033[90m    • Put Spread: ${entry_context.get('put_spread_credit', 0):.2f}\033[0m")
                        print(f"\033[90m  Max Risk/Contract: ${entry_context.get('max_risk', 0):.2f}\033[0m")
                        if 'iv_rank' in entry_context and entry_context['iv_rank'] is not None:
                            print(f"\033[90m  IV Rank: {entry_context['iv_rank']:.1f}%\033[0m")
                    
                    # Credit Spreads (Bull Put, Bear Call)
                    elif strategy_type in ['BULL_PUT_SPREAD', 'BEAR_CALL_SPREAD', 'CREDIT_SPREAD']:
                        print(f"\033[90m  ─────────────────────────────────────────\033[0m")
                        print(f"\033[90m  Strategy: {strategy_type}\033[0m")
                        print(f"\033[90m  Spread Width: ${entry_context.get('spread_width', 0):.0f}\033[0m")
                        print(f"\033[90m  Credit: ${entry_context.get('credit', 0):.2f}\033[0m")
                        print(f"\033[90m  Max Risk: ${entry_context.get('max_risk', 0):.2f}\033[0m")
                        if 'short_delta' in entry_context:
                            print(f"\033[90m  Short Delta: {entry_context['short_delta']:.3f}\033[0m")
                    
                    # Debit Spreads (Bull Call, Bear Put)
                    elif strategy_type in ['BULL_CALL_SPREAD', 'BEAR_PUT_SPREAD', 'DEBIT_SPREAD']:
                        print(f"\033[90m  ─────────────────────────────────────────\033[0m")
                        print(f"\033[90m  Strategy: {strategy_type}\033[0m")
                        print(f"\033[90m  Spread Width: ${entry_context.get('spread_width', 0):.0f}\033[0m")
                        print(f"\033[90m  Debit Paid: ${entry_context.get('debit', 0):.2f}\033[0m")
                        print(f"\033[90m  Max Profit: ${entry_context.get('max_profit', 0):.2f}\033[0m")
                    
                    # Iron Butterfly
                    elif strategy_type == 'IRON_BUTTERFLY':
                        print(f"\033[90m  ─────────────────────────────────────────\033[0m")
                        print(f"\033[90m  Strategy: IRON BUTTERFLY\033[0m")
                        print(f"\033[90m  Wing Width: ${entry_context.get('wing_width', 0):.0f}\033[0m")
                        print(f"\033[90m  ATM Strike: ${entry_context.get('atm_strike', 0):.0f}\033[0m")
                        print(f"\033[90m  Total Credit: ${entry_context.get('total_credit', 0):.2f}\033[0m")
                        print(f"\033[90m  Max Risk: ${entry_context.get('max_risk', 0):.2f}\033[0m")
                    
                    # Butterfly (Long/Short)
                    elif strategy_type in ['BUTTERFLY', 'LONG_BUTTERFLY', 'SHORT_BUTTERFLY']:
                        print(f"\033[90m  ─────────────────────────────────────────\033[0m")
                        print(f"\033[90m  Strategy: {strategy_type}\033[0m")
                        print(f"\033[90m  Wing Width: ${entry_context.get('wing_width', 0):.0f}\033[0m")
                        if 'center_strike' in entry_context:
                            print(f"\033[90m  Center Strike: ${entry_context['center_strike']:.0f}\033[0m")
                        if 'net_debit' in entry_context:
                            print(f"\033[90m  Net Debit: ${entry_context['net_debit']:.2f}\033[0m")
                        if 'net_credit' in entry_context:
                            print(f"\033[90m  Net Credit: ${entry_context['net_credit']:.2f}\033[0m")
                        if 'max_profit' in entry_context:
                            print(f"\033[90m  Max Profit: ${entry_context['max_profit']:.2f}\033[0m")
                    
                    # Calendar Spread
                    elif strategy_type == 'CALENDAR_SPREAD':
                        print(f"\033[90m  ─────────────────────────────────────────\033[0m")
                        print(f"\033[90m  Strategy: CALENDAR SPREAD\033[0m")
                        print(f"\033[90m  Front DTE: {entry_context.get('front_dte', 0):.0f} days\033[0m")
                        print(f"\033[90m  Back DTE: {entry_context.get('back_dte', 0):.0f} days\033[0m")
                        if 'strike' in entry_context:
                            print(f"\033[90m  Strike: ${entry_context['strike']:.0f}\033[0m")
                        if 'net_debit' in entry_context:
                            print(f"\033[90m  Net Debit: ${entry_context['net_debit']:.2f}\033[0m")
                    
                    # Diagonal Spread
                    elif strategy_type == 'DIAGONAL_SPREAD':
                        print(f"\033[90m  ─────────────────────────────────────────\033[0m")
                        print(f"\033[90m  Strategy: DIAGONAL SPREAD\033[0m")
                        print(f"\033[90m  Front DTE: {entry_context.get('front_dte', 0):.0f} days\033[0m")
                        print(f"\033[90m  Back DTE: {entry_context.get('back_dte', 0):.0f} days\033[0m")
                        if 'strike_offset' in entry_context:
                            print(f"\033[90m  Strike Offset: ${entry_context['strike_offset']:.0f}\033[0m")
                        if 'front_strike' in entry_context:
                            print(f"\033[90m  Front Strike: ${entry_context['front_strike']:.0f}\033[0m")
                        if 'back_strike' in entry_context:
                            print(f"\033[90m  Back Strike: ${entry_context['back_strike']:.0f}\033[0m")
                        if 'net_debit' in entry_context:
                            print(f"\033[90m  Net Debit: ${entry_context['net_debit']:.2f}\033[0m")
                    
                    # Covered Call
                    elif strategy_type == 'COVERED_CALL':
                        print(f"\033[90m  ─────────────────────────────────────────\033[0m")
                        print(f"\033[90m  Strategy: COVERED CALL\033[0m")
                        print(f"\033[90m  Stock Price: ${entry_context.get('stock_price', 0):.2f}\033[0m")
                        print(f"\033[90m  Call Strike: ${entry_context.get('call_strike', 0):.0f}\033[0m")
                        print(f"\033[90m  Call Premium: ${entry_context.get('call_premium', 0):.2f}\033[0m")
                        print(f"\033[90m  Call Delta: {entry_context.get('call_delta', 0):.3f}\033[0m")
                    
                    # Straddle/Strangle details
                    elif 'call_bid' in entry_context and 'put_bid' in entry_context:
                        print(f"\033[90m  ─────────────────────────────────────────\033[0m")
                        if strategy_type:
                            print(f"\033[90m  Strategy: {strategy_type}\033[0m")
                        print(f"\033[90m  Call bid: ${entry_context['call_bid']:.2f}, Put bid: ${entry_context['put_bid']:.2f}\033[0m")
                        if 'strike' in entry_context:
                            print(f"\033[90m  Strike: ${entry_context['strike']:.0f}\033[0m")
                    
                    # Generic fallback: show any strategy_type
                    elif strategy_type:
                        print(f"\033[90m  ─────────────────────────────────────────\033[0m")
                        print(f"\033[90m  Strategy: {strategy_type}\033[0m")
                    
                    # Z-score for mean reversion strategies - check for None
                    if 'z_score' in entry_context and entry_context['z_score'] is not None:
                        print(f"\033[90m  Z-score: {entry_context['z_score']:.2f}\033[0m")
                    
                    # IV Rank (universal) - check for None to avoid TypeError
                    if 'iv_rank' in entry_context and entry_context['iv_rank'] is not None and strategy_type != 'IRON_CONDOR':
                        print(f"\033[90m  IV Rank: {entry_context['iv_rank']:.1f}%\033[0m")
        
        return {
            'num_contracts': num_contracts,
            'target_allocation': target_allocation,
            'actual_allocation': actual_allocation,
            'total_capital': capital_info['total_capital'],
            'available_capital': capital_info['available_capital'],
            'capital_at_risk': capital_info['capital_at_risk'],
            'locked_capital': capital_info['locked_capital'],
            'unrealized_pnl': capital_info['unrealized_pnl'],
            'open_positions_count': capital_info['open_positions_count'],
            'allocation_pct_of_total': allocation_pct_of_total,
            'allocation_pct_of_available': allocation_pct_of_available
        }
    
    def close_all_positions(self, final_date, price_data, reason='end_of_backtest', 
                          get_detailed_data=None):
        """
        Close all open positions at end of backtest
        
        Args:
            final_date: Final date
            price_data: Price data dict {position_id: price or dict with price/pnl}
            reason: Close reason (default: 'end_of_backtest')
            get_detailed_data: Optional callback function(position) -> dict
                              Returns detailed exit data (Greeks, IV, bid/ask, etc.)
                              Used for options positions requiring detailed export
        """
        for position_id in list(self.positions.keys()):
            position = self.positions[position_id]
            
            # Check if this is an options position (has expiration date)
            is_option = position.get('expiration') is not None
            
            # Get price data
            if position_id in price_data:
                if isinstance(price_data[position_id], dict):
                    data = price_data[position_id]
                    exit_price = data.get('price', position['entry_price'])
                    pnl = data.get('pnl', None)
                else:
                    exit_price = price_data[position_id]
                    pnl = None
                
                if pnl is None and position['entry_price'] == 0:
                    if isinstance(price_data[position_id], dict) and 'pnl' in price_data[position_id]:
                        pnl = price_data[position_id]['pnl']
            else:
                # No price data - use entry price
                exit_price = position['entry_price']
                pnl = 0
                data = {}
            
            # Get detailed data for options (if callback provided)
            detailed_kwargs = {}
            if is_option and get_detailed_data is not None:
                try:
                    detailed_kwargs = get_detailed_data(position)
                    if detailed_kwargs and isinstance(detailed_kwargs, dict):
                        # Merge detailed data into kwargs
                        if 'pnl' in detailed_kwargs and pnl is None:
                            pnl = detailed_kwargs.pop('pnl')
                except Exception as e:
                    if self.debug:
                        print(f"[PositionManager] ⚠️  get_detailed_data failed for {position_id}: {e}")
            
            # Also pass data from price_data if it's a dict
            if isinstance(price_data.get(position_id), dict):
                for key, value in price_data[position_id].items():
                    if key not in ['price', 'pnl', 'pnl_pct'] and key not in detailed_kwargs:
                        detailed_kwargs[key] = value
            
            self.close_position(
                position_id=position_id,
                exit_date=final_date,
                exit_price=exit_price,
                close_reason=reason,
                pnl=pnl,
                **detailed_kwargs
            )


# ============================================================
# BACKTEST ANALYZER (unchanged)
# ============================================================
class BacktestAnalyzer:
    """Calculate all metrics from BacktestResults"""
    
    def __init__(self, results):
        self.results = results
        self.metrics = {}
    
    def calculate_all_metrics(self):
        r = self.results
        
        self.metrics['initial_capital'] = r.initial_capital
        self.metrics['final_equity'] = r.final_capital
        
        self.metrics['total_pnl'] = r.final_capital - r.initial_capital
        self.metrics['total_return'] = (self.metrics['total_pnl'] / r.initial_capital) * 100
        
        if len(r.equity_dates) > 0:
            start_date = min(r.equity_dates)
            end_date = max(r.equity_dates)
            days_diff = (end_date - start_date).days
            
            if days_diff <= 0:
                self.metrics['cagr'] = 0
                self.metrics['show_cagr'] = False
            else:
                years = days_diff / 365.25
                if years >= 1.0:
                    self.metrics['cagr'] = ((r.final_capital / r.initial_capital) ** (1/years) - 1) * 100
                    self.metrics['show_cagr'] = True
                else:
                    self.metrics['cagr'] = self.metrics['total_return'] * (365.25 / days_diff)
                    self.metrics['show_cagr'] = False
        else:
            self.metrics['cagr'] = 0
            self.metrics['show_cagr'] = False
        
        self.metrics['sharpe'] = self._sharpe_ratio(r.daily_returns)
        self.metrics['sortino'] = self._sortino_ratio(r.daily_returns)
        self.metrics['max_drawdown'] = r.max_drawdown
        self.metrics['volatility'] = np.std(r.daily_returns) * np.sqrt(252) * 100 if len(r.daily_returns) > 0 else 0
        self.metrics['calmar'] = abs(self.metrics['total_return'] / r.max_drawdown) if r.max_drawdown > 0 else 0
        self.metrics['omega'] = self._omega_ratio(r.daily_returns)
        self.metrics['ulcer'] = self._ulcer_index(r.equity_curve)
        
        self.metrics['var_95'], self.metrics['var_95_pct'] = self._calculate_var(r.daily_returns, 0.95)
        self.metrics['var_99'], self.metrics['var_99_pct'] = self._calculate_var(r.daily_returns, 0.99)
        self.metrics['cvar_95'], self.metrics['cvar_95_pct'] = self._calculate_cvar(r.daily_returns, 0.95)
        
        avg_equity = np.mean(r.equity_curve) if len(r.equity_curve) > 0 else r.initial_capital
        self.metrics['var_95_dollar'] = self.metrics['var_95'] * avg_equity
        self.metrics['var_99_dollar'] = self.metrics['var_99'] * avg_equity
        self.metrics['cvar_95_dollar'] = self.metrics['cvar_95'] * avg_equity
        
        self.metrics['tail_ratio'] = self._tail_ratio(r.daily_returns)
        self.metrics['skewness'], self.metrics['kurtosis'] = self._skewness_kurtosis(r.daily_returns)
        
        self.metrics['alpha'], self.metrics['beta'], self.metrics['r_squared'] = self._alpha_beta(r)
        
        if len(r.trades) > 0:
            self._calculate_trading_stats(r.trades)
        else:
            self._set_empty_trading_stats()
        
        # Calculate recovery factor (only if equity_curve has data)
        if len(r.equity_curve) > 0:
            running_max = np.maximum.accumulate(r.equity_curve)
            max_dd_dollars = np.min(np.array(r.equity_curve) - running_max)
            self.metrics['recovery_factor'] = self.metrics['total_pnl'] / abs(max_dd_dollars) if max_dd_dollars != 0 else 0
        else:
            self.metrics['recovery_factor'] = 0
        
        if len(r.trades) > 0 and 'start_date' in r.config and 'end_date' in r.config:
            total_days = (pd.to_datetime(r.config['end_date']) - pd.to_datetime(r.config['start_date'])).days
            self.metrics['exposure_time'] = self._exposure_time(r.trades, total_days)
        else:
            self.metrics['exposure_time'] = 0
        
        # Calculate exit type metrics (stop-loss, profit target, expiration, signal exits)
        calculate_stoploss_metrics(self)
        
        return self.metrics
    
    def _calculate_trading_stats(self, trades):
        trades_df = pd.DataFrame(trades)
        winning = trades_df[trades_df['pnl'] > 0]
        losing = trades_df[trades_df['pnl'] <= 0]
        
        self.metrics['total_trades'] = len(trades_df)
        self.metrics['winning_trades'] = len(winning)
        self.metrics['losing_trades'] = len(losing)
        self.metrics['win_rate'] = (len(winning) / len(trades_df)) * 100 if len(trades_df) > 0 else 0
        
        wins_sum = winning['pnl'].sum() if len(winning) > 0 else 0
        losses_sum = abs(losing['pnl'].sum()) if len(losing) > 0 else 0
        self.metrics['profit_factor'] = wins_sum / losses_sum if losses_sum > 0 else float('inf')
        
        self.metrics['avg_win'] = winning['pnl'].mean() if len(winning) > 0 else 0
        self.metrics['avg_loss'] = losing['pnl'].mean() if len(losing) > 0 else 0
        self.metrics['best_trade'] = trades_df['pnl'].max()
        self.metrics['worst_trade'] = trades_df['pnl'].min()
        
        if len(winning) > 0 and len(losing) > 0 and self.metrics['avg_loss'] != 0:
            self.metrics['avg_win_loss_ratio'] = abs(self.metrics['avg_win'] / self.metrics['avg_loss'])
        else:
            self.metrics['avg_win_loss_ratio'] = 0
        
        self.metrics['max_win_streak'], self.metrics['max_loss_streak'] = self._win_loss_streaks(trades)
    
    def _set_empty_trading_stats(self):
        self.metrics.update({
            'total_trades': 0, 'winning_trades': 0, 'losing_trades': 0,
            'win_rate': 0, 'profit_factor': 0, 'avg_win': 0, 'avg_loss': 0,
            'best_trade': 0, 'worst_trade': 0, 'avg_win_loss_ratio': 0,
            'max_win_streak': 0, 'max_loss_streak': 0
        })
    
    def _sharpe_ratio(self, returns):
        if len(returns) < 2:
            return 0
        return np.sqrt(252) * np.mean(returns) / np.std(returns) if np.std(returns) > 0 else 0
    
    def _sortino_ratio(self, returns):
        if len(returns) < 2:
            return 0
        returns_array = np.array(returns)
        downside = returns_array[returns_array < 0]
        if len(downside) == 0 or np.std(downside) == 0:
            return 0
        return np.sqrt(252) * np.mean(returns_array) / np.std(downside)
    
    def _omega_ratio(self, returns, threshold=0):
        if len(returns) < 2:
            return 0
        returns_array = np.array(returns)
        gains = np.sum(np.maximum(returns_array - threshold, 0))
        losses = np.sum(np.maximum(threshold - returns_array, 0))
        return gains / losses if losses > 0 else float('inf')
    
    def _ulcer_index(self, equity_curve):
        if len(equity_curve) < 2:
            return 0
        equity_array = np.array(equity_curve)
        running_max = np.maximum.accumulate(equity_array)
        drawdown = (equity_array - running_max) / running_max
        return np.sqrt(np.mean(drawdown ** 2)) * 100
    
    def _calculate_var(self, returns, confidence=0.95):
        if len(returns) < 10:
            return 0, 0
        returns_array = np.array(returns)
        returns_array = returns_array[~np.isnan(returns_array)]
        if len(returns_array) < 10:
            return 0, 0
        var_percentile = (1 - confidence) * 100
        var_return = np.percentile(returns_array, var_percentile)
        return var_return, var_return * 100
    
    def _calculate_cvar(self, returns, confidence=0.95):
        if len(returns) < 10:
            return 0, 0
        returns_array = np.array(returns)
        returns_array = returns_array[~np.isnan(returns_array)]
        if len(returns_array) < 10:
            return 0, 0
        var_percentile = (1 - confidence) * 100
        var_threshold = np.percentile(returns_array, var_percentile)
        tail_losses = returns_array[returns_array <= var_threshold]
        if len(tail_losses) == 0:
            return 0, 0
        cvar_return = np.mean(tail_losses)
        return cvar_return, cvar_return * 100
    
    def _tail_ratio(self, returns):
        if len(returns) < 20:
            return 0
        returns_array = np.array(returns)
        right = np.percentile(returns_array, 95)
        left = abs(np.percentile(returns_array, 5))
        return right / left if left > 0 else 0
    
    def _skewness_kurtosis(self, returns):
        if len(returns) < 10:
            return 0, 0
        returns_array = np.array(returns)
        mean = np.mean(returns_array)
        std = np.std(returns_array)
        if std == 0:
            return 0, 0
        skew = np.mean(((returns_array - mean) / std) ** 3)
        kurt = np.mean(((returns_array - mean) / std) ** 4) - 3
        return skew, kurt
    
    def _alpha_beta(self, results):
        if not hasattr(results, 'benchmark_prices'):
            return 0, 0, 0
        if not results.benchmark_prices or len(results.equity_dates) < 10:
            return 0, 0, 0
        
        benchmark_returns = []
        sorted_dates = sorted(results.equity_dates)
        
        for i in range(1, len(sorted_dates)):
            prev_date = sorted_dates[i-1]
            curr_date = sorted_dates[i]
            
            if prev_date in results.benchmark_prices and curr_date in results.benchmark_prices:
                prev_price = results.benchmark_prices[prev_date]
                curr_price = results.benchmark_prices[curr_date]
                bench_return = (curr_price - prev_price) / prev_price
                benchmark_returns.append(bench_return)
            else:
                benchmark_returns.append(0)
        
        if len(benchmark_returns) != len(results.daily_returns):
            return 0, 0, 0
        
        port_ret = np.array(results.daily_returns)
        bench_ret = np.array(benchmark_returns)
        
        bench_mean = np.mean(bench_ret)
        port_mean = np.mean(port_ret)
        
        covariance = np.mean((bench_ret - bench_mean) * (port_ret - port_mean))
        benchmark_variance = np.mean((bench_ret - bench_mean) ** 2)
        
        if benchmark_variance == 0:
            return 0, 0, 0
        
        beta = covariance / benchmark_variance
        alpha_daily = port_mean - beta * bench_mean
        alpha_annualized = alpha_daily * 252 * 100
        
        ss_res = np.sum((port_ret - (alpha_daily + beta * bench_ret)) ** 2)
        ss_tot = np.sum((port_ret - port_mean) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        return alpha_annualized, beta, r_squared
    
    def _win_loss_streaks(self, trades):
        if len(trades) == 0:
            return 0, 0
        max_win = max_loss = current_win = current_loss = 0
        for trade in trades:
            if trade['pnl'] > 0:
                current_win += 1
                current_loss = 0
                max_win = max(max_win, current_win)
            else:
                current_loss += 1
                current_win = 0
                max_loss = max(max_loss, current_loss)
        return max_win, max_loss
    
    def _exposure_time(self, trades, total_days):
        if total_days <= 0 or len(trades) == 0:
            return 0
        days_with_positions = set()
        for trade in trades:
            entry = pd.to_datetime(trade['entry_date'])
            exit_ = pd.to_datetime(trade['exit_date'])
            date_range = pd.date_range(start=entry, end=exit_, freq='D')
            days_with_positions.update(date_range.date)
        exposure_pct = (len(days_with_positions) / total_days) * 100
        return min(exposure_pct, 100.0)


# ============================================================
# STOP-LOSS METRICS (unchanged)
# ============================================================
def calculate_stoploss_metrics(analyzer):
    """Calculate stop-loss specific metrics"""
    if len(analyzer.results.trades) == 0:
        _set_empty_stoploss_metrics(analyzer)
        return analyzer.metrics
    
    trades_df = pd.DataFrame(analyzer.results.trades)
    
    if 'exit_reason' not in trades_df.columns:
        _set_empty_stoploss_metrics(analyzer)
        return analyzer.metrics
    
    sl_trades = trades_df[trades_df['exit_reason'].str.contains('stop_loss', na=False)]
    profit_target_trades = trades_df[trades_df['exit_reason'] == 'profit_target']
    
    analyzer.metrics['stoploss_count'] = len(sl_trades)
    analyzer.metrics['stoploss_pct'] = (len(sl_trades) / len(trades_df)) * 100 if len(trades_df) > 0 else 0
    analyzer.metrics['profit_target_count'] = len(profit_target_trades)
    analyzer.metrics['profit_target_pct'] = (len(profit_target_trades) / len(trades_df)) * 100 if len(trades_df) > 0 else 0
    
    # Expiration and Signal exits
    expiration_trades = trades_df[trades_df['exit_reason'] == 'expiration']
    signal_exit_trades = trades_df[trades_df['exit_reason'].str.contains('z_score_exit|signal_exit|reversion', na=False, regex=True)]
    analyzer.metrics['expiration_count'] = len(expiration_trades)
    analyzer.metrics['signal_exit_count'] = len(signal_exit_trades)
    
    if len(sl_trades) > 0:
        analyzer.metrics['avg_stoploss_pnl'] = sl_trades['pnl'].mean()
        analyzer.metrics['total_stoploss_loss'] = sl_trades['pnl'].sum()
        analyzer.metrics['worst_stoploss'] = sl_trades['pnl'].min()
        
        if 'return_pct' in sl_trades.columns:
            analyzer.metrics['avg_stoploss_return_pct'] = sl_trades['return_pct'].mean()
        else:
            analyzer.metrics['avg_stoploss_return_pct'] = 0
        
        if 'entry_date' in sl_trades.columns and 'exit_date' in sl_trades.columns:
            sl_trades_copy = sl_trades.copy()
            sl_trades_copy['entry_date'] = pd.to_datetime(sl_trades_copy['entry_date'])
            sl_trades_copy['exit_date'] = pd.to_datetime(sl_trades_copy['exit_date'])
            sl_trades_copy['days_held'] = (sl_trades_copy['exit_date'] - sl_trades_copy['entry_date']).dt.days
            analyzer.metrics['avg_days_to_stoploss'] = sl_trades_copy['days_held'].mean()
            analyzer.metrics['min_days_to_stoploss'] = sl_trades_copy['days_held'].min()
            analyzer.metrics['max_days_to_stoploss'] = sl_trades_copy['days_held'].max()
        else:
            analyzer.metrics['avg_days_to_stoploss'] = 0
            analyzer.metrics['min_days_to_stoploss'] = 0
            analyzer.metrics['max_days_to_stoploss'] = 0
        
        if 'stop_type' in sl_trades.columns:
            stop_types = sl_trades['stop_type'].value_counts().to_dict()
            analyzer.metrics['stoploss_by_type'] = stop_types
        else:
            analyzer.metrics['stoploss_by_type'] = {}
    else:
        analyzer.metrics['avg_stoploss_pnl'] = 0
        analyzer.metrics['total_stoploss_loss'] = 0
        analyzer.metrics['worst_stoploss'] = 0
        analyzer.metrics['avg_stoploss_return_pct'] = 0
        analyzer.metrics['avg_days_to_stoploss'] = 0
        analyzer.metrics['min_days_to_stoploss'] = 0
        analyzer.metrics['max_days_to_stoploss'] = 0
        analyzer.metrics['stoploss_by_type'] = {}
    
    if len(profit_target_trades) > 0 and len(sl_trades) > 0:
        avg_profit_target = profit_target_trades['pnl'].mean()
        avg_stoploss = abs(sl_trades['pnl'].mean())
        analyzer.metrics['profit_to_loss_ratio'] = avg_profit_target / avg_stoploss if avg_stoploss > 0 else 0
    else:
        analyzer.metrics['profit_to_loss_ratio'] = 0
    
    if 'max_profit_before_stop' in sl_trades.columns:
        early_exits = sl_trades[sl_trades['max_profit_before_stop'] > 0]
        analyzer.metrics['early_exit_count'] = len(early_exits)
        analyzer.metrics['early_exit_pct'] = (len(early_exits) / len(sl_trades)) * 100 if len(sl_trades) > 0 else 0
        if len(early_exits) > 0:
            analyzer.metrics['avg_missed_profit'] = early_exits['max_profit_before_stop'].mean()
        else:
            analyzer.metrics['avg_missed_profit'] = 0
    else:
        analyzer.metrics['early_exit_count'] = 0
        analyzer.metrics['early_exit_pct'] = 0
        analyzer.metrics['avg_missed_profit'] = 0
    
    exit_reasons = trades_df['exit_reason'].value_counts().to_dict()
    analyzer.metrics['exit_reasons'] = exit_reasons
    
    return analyzer.metrics


def _set_empty_stoploss_metrics(analyzer):
    analyzer.metrics.update({
        'stoploss_count': 0, 'stoploss_pct': 0,
        'profit_target_count': 0, 'profit_target_pct': 0,
        'expiration_count': 0, 'signal_exit_count': 0,
        'avg_stoploss_pnl': 0, 'total_stoploss_loss': 0,
        'worst_stoploss': 0, 'avg_stoploss_return_pct': 0,
        'avg_days_to_stoploss': 0, 'min_days_to_stoploss': 0,
        'max_days_to_stoploss': 0, 'stoploss_by_type': {},
        'profit_to_loss_ratio': 0, 'early_exit_count': 0,
        'early_exit_pct': 0, 'avg_missed_profit': 0,
        'exit_reasons': {}
    })


# ============================================================
# RESULTS REPORTER (unchanged)
# ============================================================
class ResultsReporter:
    """Print comprehensive metrics report"""
    
    @staticmethod
    def print_full_report(analyzer):
        m = analyzer.metrics
        r = analyzer.results
        
        print("="*80)
        print(" "*25 + "BACKTEST RESULTS")
        print("="*80)
        print()
        
        print("PROFITABILITY METRICS")
        print("-"*80)
        print(f"Initial Capital:        ${r.initial_capital:>15,.2f}")
        print(f"Final Equity:           ${r.final_capital:>15,.2f}")
        print(f"Total P&L:              ${m['total_pnl']:>15,.2f}  (absolute profit/loss)")
        print(f"Total Return:            {m['total_return']:>15.2f}%  (% gain/loss)")
        if m['cagr'] != 0:
            if m['show_cagr']:
                print(f"CAGR:                    {m['cagr']:>15.2f}%  (annualized compound growth)")
            else:
                print(f"Annualized Return:       {m['cagr']:>15.2f}%  (extrapolated to 1 year)")
        print()
        
        print("RISK METRICS")
        print("-"*80)
        print(f"Sharpe Ratio:            {m['sharpe']:>15.2f}  (>1 good, >2 excellent)")
        print(f"Sortino Ratio:           {m['sortino']:>15.2f}  (downside risk, >2 good)")
        print(f"Calmar Ratio:            {m['calmar']:>15.2f}  (return/drawdown, >3 good)")
        if m['omega'] != 0:
            omega_display = f"{m['omega']:.2f}" if m['omega'] < 999 else "∞"
            print(f"Omega Ratio:             {omega_display:>15s}  (gains/losses, >1 good)")
        print(f"Maximum Drawdown:        {m['max_drawdown']:>15.2f}%  (peak to trough)")
        if m['ulcer'] != 0:
            print(f"Ulcer Index:             {m['ulcer']:>15.2f}%  (pain of drawdowns, lower better)")
        print(f"Volatility (ann.):       {m['volatility']:>15.2f}%  (annualized std dev)")
        
        if len(r.daily_returns) >= 10:
            print(f"VaR (95%, 1-day):        {m['var_95_pct']:>15.2f}% (${m['var_95_dollar']:>,.0f})  (max loss 95% confidence)")
            print(f"VaR (99%, 1-day):        {m['var_99_pct']:>15.2f}% (${m['var_99_dollar']:>,.0f})  (max loss 99% confidence)")
            print(f"CVaR (95%, 1-day):       {m['cvar_95_pct']:>15.2f}% (${m['cvar_95_dollar']:>,.0f})  (avg loss in worst 5%)")
        
        if m['tail_ratio'] != 0:
            print(f"Tail Ratio (95/5):       {m['tail_ratio']:>15.2f}  (big wins/losses, >1 good)")
        
        if m['skewness'] != 0 or m['kurtosis'] != 0:
            print(f"Skewness:                {m['skewness']:>15.2f}  (>0 positive tail)")
            print(f"Kurtosis (excess):       {m['kurtosis']:>15.2f}  (>0 fat tails)")
        
        if m['beta'] != 0 or m['alpha'] != 0:
            print(f"Alpha (vs {r.benchmark_symbol}):     {m['alpha']:>15.2f}%  (excess return)")
            print(f"Beta (vs {r.benchmark_symbol}):      {m['beta']:>15.2f}  (<1 defensive, >1 aggressive)")
            print(f"R² (vs {r.benchmark_symbol}):        {m['r_squared']:>15.2f}  (market correlation 0-1)")
        
        if abs(m['total_return']) > 200 or m['volatility'] > 150:
            print()
            print("WARNING: UNREALISTIC RESULTS DETECTED")
            if abs(m['total_return']) > 200:
                print(f"  Total return {m['total_return']:.1f}% is extremely high")
            if m['volatility'] > 150:
                print(f"  Volatility {m['volatility']:.1f}% is higher than leveraged ETFs")
            print("  Review configuration before trusting results")
        
        print()
        
        print("EFFICIENCY METRICS")
        print("-"*80)
        if m['recovery_factor'] != 0:
            print(f"Recovery Factor:         {m['recovery_factor']:>15.2f}  (profit/max DD, >3 good)")
        if m['exposure_time'] != 0:
            print(f"Exposure Time:           {m['exposure_time']:>15.1f}%  (time in market)")
        print()
        
        print("TRADING STATISTICS")
        print("-"*80)
        print(f"Total Trades:            {m['total_trades']:>15}")
        print(f"Winning Trades:          {m['winning_trades']:>15}")
        print(f"Losing Trades:           {m['losing_trades']:>15}")
        print(f"Win Rate:                {m['win_rate']:>15.2f}%  (% profitable trades)")
        print(f"Profit Factor:           {m['profit_factor']:>15.2f}  (gross profit/loss, >1.5 good)")
        if m['max_win_streak'] > 0 or m['max_loss_streak'] > 0:
            print(f"Max Win Streak:          {m['max_win_streak']:>15}  (consecutive wins)")
            print(f"Max Loss Streak:         {m['max_loss_streak']:>15}  (consecutive losses)")
        print(f"Average Win:            ${m['avg_win']:>15,.2f}")
        print(f"Average Loss:           ${m['avg_loss']:>15,.2f}")
        print(f"Best Trade:             ${m['best_trade']:>15,.2f}")
        print(f"Worst Trade:            ${m['worst_trade']:>15,.2f}")
        if m['avg_win_loss_ratio'] != 0:
            print(f"Avg Win/Loss Ratio:      {m['avg_win_loss_ratio']:>15.2f}  (avg win / avg loss)")
        print()
        
        # Exit Types Breakdown
        print("EXIT TYPES")
        print("-"*80)
        print(f"Stop-Loss Exits:         {m.get('stoploss_count', 0):>15}")
        print(f"Profit Target Exits:     {m.get('profit_target_count', 0):>15}")
        print(f"Expiration Exits:        {m.get('expiration_count', 0):>15}")
        print(f"Signal Exits:            {m.get('signal_exit_count', 0):>15}")
        print()
        print("="*80)


def print_stoploss_section(analyzer):
    """Print stop-loss analysis section"""
    m = analyzer.metrics
    
    if m.get('stoploss_count', 0) == 0:
        return
    
    print("STOP-LOSS ANALYSIS")
    print("-"*80)
    
    print(f"Stop-Loss Trades:        {m['stoploss_count']:>15}  ({m['stoploss_pct']:.1f}% of total)")
    print(f"Profit Target Trades:    {m['profit_target_count']:>15}  ({m['profit_target_pct']:.1f}% of total)")
    
    print(f"Avg Stop-Loss P&L:      ${m['avg_stoploss_pnl']:>15,.2f}")
    print(f"Total Loss from SL:     ${m['total_stoploss_loss']:>15,.2f}")
    print(f"Worst Stop-Loss:        ${m['worst_stoploss']:>15,.2f}")
    print(f"Avg SL Return:           {m['avg_stoploss_return_pct']:>15.2f}%")
    
    if m['avg_days_to_stoploss'] > 0:
        print(f"Avg Days to SL:          {m['avg_days_to_stoploss']:>15.1f}")
        print(f"Min/Max Days to SL:      {m['min_days_to_stoploss']:>7} / {m['max_days_to_stoploss']:<7}")
    
    if m['profit_to_loss_ratio'] > 0:
        print(f"Profit/Loss Ratio:       {m['profit_to_loss_ratio']:>15.2f}  (avg profit target / avg stop-loss)")
    
    if m['early_exit_count'] > 0:
        print(f"Early Exits:             {m['early_exit_count']:>15}  ({m['early_exit_pct']:.1f}% of SL trades)")
        print(f"Avg Missed Profit:      ${m['avg_missed_profit']:>15,.2f}  (profit before stop triggered)")
    
    if m['stoploss_by_type']:
        print(f"\nStop-Loss Types:")
        for stop_type, count in m['stoploss_by_type'].items():
            pct = (count / m['stoploss_count']) * 100
            print(f"  {stop_type:20s} {count:>5} trades ({pct:.1f}%)")
    
    if m.get('exit_reasons'):
        print(f"\nExit Reasons Distribution:")
        total_trades = sum(m['exit_reasons'].values())
        for reason, count in sorted(m['exit_reasons'].items(), key=lambda x: x[1], reverse=True):
            pct = (count / total_trades) * 100
            print(f"  {reason:20s} {count:>5} trades ({pct:.1f}%)")
    
    print()
    print("="*80)


# ============================================================
# CHART GENERATOR (only core charts, optimization charts separate)
# ============================================================
class ChartGenerator:
    """Generate comprehensive multi-panel performance charts"""
    
    @staticmethod
    def create_all_charts(analyzer, filename='backtest_results.png', show_plots=True, silent=False):
        """
        Create a 6-panel chart with equity curve, drawdown, monthly returns, and metrics.
        
        Args:
            analyzer (BacktestAnalyzer): Analyzer instance with calculated metrics
            filename (str): Output PNG filename (default: 'backtest_results.png')
            show_plots (bool): If True, display chart in notebook; if False, save only
            silent (bool): If True, suppress print output
        
        Returns:
            None (saves chart to disk as PNG)
        
        Generated panels:
            1. Equity curve with drawdown overlay
            2. Monthly returns heatmap
            3. Trade distribution histogram  
            4. Win/loss analysis
            5. Rolling Sharpe ratio
            6. Key metrics summary box
        """
        r = analyzer.results
        
        if len(r.trades) == 0:
            if not silent:
                print("No trades to visualize")
            return None
        
        trades_df = pd.DataFrame(r.trades)
        fig, axes = plt.subplots(3, 2, figsize=(18, 14))
        fig.suptitle('Backtest Results', fontsize=16, fontweight='bold', y=0.995)
        
        dates = pd.to_datetime(r.equity_dates)
        equity_array = np.array(r.equity_curve)
        
        ax1 = axes[0, 0]
        ax1.plot(dates, equity_array, linewidth=2.5, color='#2196F3')
        ax1.axhline(y=r.initial_capital, color='gray', linestyle='--', alpha=0.7)
        ax1.fill_between(dates, r.initial_capital, equity_array,
                         where=(equity_array >= r.initial_capital), 
                         alpha=0.3, color='green', interpolate=True)
        ax1.fill_between(dates, r.initial_capital, equity_array,
                         where=(equity_array < r.initial_capital), 
                         alpha=0.3, color='red', interpolate=True)
        ax1.set_title('Equity Curve', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Equity ($)')
        ax1.grid(True, alpha=0.3)
        
        ax2 = axes[0, 1]
        running_max = np.maximum.accumulate(equity_array)
        drawdown = (equity_array - running_max) / running_max * 100
        ax2.fill_between(dates, 0, drawdown, alpha=0.6, color='#f44336')
        ax2.plot(dates, drawdown, color='#d32f2f', linewidth=2)
        ax2.set_title('Drawdown', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Drawdown (%)')
        ax2.grid(True, alpha=0.3)
        
        ax3 = axes[1, 0]
        pnl_values = trades_df['pnl'].values
        ax3.hist(pnl_values, bins=40, color='#4CAF50', alpha=0.7, edgecolor='black')
        ax3.axvline(x=0, color='red', linestyle='--', linewidth=2)
        ax3.set_title('P&L Distribution', fontsize=12, fontweight='bold')
        ax3.set_xlabel('P&L ($)')
        ax3.grid(True, alpha=0.3, axis='y')
        
        ax4 = axes[1, 1]
        if 'signal' in trades_df.columns:
            signal_pnl = trades_df.groupby('signal')['pnl'].sum()
            colors = ['#4CAF50' if x > 0 else '#f44336' for x in signal_pnl.values]
            ax4.bar(signal_pnl.index, signal_pnl.values, color=colors, alpha=0.7)
            ax4.set_title('P&L by Signal', fontsize=12, fontweight='bold')
        else:
            ax4.text(0.5, 0.5, 'No signal data', ha='center', va='center', transform=ax4.transAxes)
        ax4.axhline(y=0, color='black', linewidth=1)
        ax4.grid(True, alpha=0.3, axis='y')
        
        ax5 = axes[2, 0]
        trades_df['exit_date'] = pd.to_datetime(trades_df['exit_date'])
        trades_df['month'] = trades_df['exit_date'].dt.to_period('M')
        monthly_pnl = trades_df.groupby('month')['pnl'].sum()
        colors = ['#4CAF50' if x > 0 else '#f44336' for x in monthly_pnl.values]
        ax5.bar(range(len(monthly_pnl)), monthly_pnl.values, color=colors, alpha=0.7)
        ax5.set_title('Monthly P&L', fontsize=12, fontweight='bold')
        ax5.set_xticks(range(len(monthly_pnl)))
        ax5.set_xticklabels([str(m) for m in monthly_pnl.index], rotation=45, ha='right')
        ax5.axhline(y=0, color='black', linewidth=1)
        ax5.grid(True, alpha=0.3, axis='y')
        
        ax6 = axes[2, 1]
        if 'symbol' in trades_df.columns:
            symbol_pnl = trades_df.groupby('symbol')['pnl'].sum().sort_values(ascending=True).tail(10)
            colors = ['#4CAF50' if x > 0 else '#f44336' for x in symbol_pnl.values]
            ax6.barh(range(len(symbol_pnl)), symbol_pnl.values, color=colors, alpha=0.7)
            ax6.set_yticks(range(len(symbol_pnl)))
            ax6.set_yticklabels(symbol_pnl.index, fontsize=9)
            ax6.set_title('Top Symbols', fontsize=12, fontweight='bold')
        else:
            ax6.text(0.5, 0.5, 'No symbol data', ha='center', va='center', transform=ax6.transAxes)
        ax6.axvline(x=0, color='black', linewidth=1)
        ax6.grid(True, alpha=0.3, axis='x')
        
        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        
        if show_plots:
            plt.show()
        else:
            plt.close()  # Close without displaying
        
        if not silent:
            print(f"Chart saved: {filename}")
        
        return filename
    
    @staticmethod
    def create_optimization_summary(results_df, metric='sharpe', filename='optimization_summary.png', 
                                    show_plots=True, silent=False):
        """
        Create 6-panel optimization summary chart.
        
        Panels:
            1. Sharpe vs Return (colored by drawdown, sized by trades)
            2. Win Rate vs Profit Factor (colored by Sharpe)
            3. Sharpe distribution histogram
            4. Trade counts distribution
            5. Top 10 combinations by metric
            6. Parameter heatmap (if exactly 2 params)
        
        Args:
            results_df: DataFrame with optimization results
            metric: Optimization metric ('sharpe', 'total_return', etc.)
            filename: Output filename
            show_plots: If True, display chart
            silent: If True, suppress print output
        
        Returns:
            str: Path to saved chart, or None if failed
        
        Example:
            chart_path = ChartGenerator.create_optimization_summary(
                results_df, metric='sharpe',
                filename=os.path.join(folder, 'optimization_summary.png')
            )
        """
        try:
            import matplotlib.pyplot as plt
            import seaborn as sns
            sns.set_style("whitegrid")
            
            # Create figure with 6 subplots
            fig = plt.figure(figsize=(20, 12))
            fig.suptitle('Optimization Results Summary', fontsize=16, fontweight='bold', y=0.995)
            
            # 1. Sharpe vs Return (colored by drawdown, sized by trades)
            ax1 = plt.subplot(2, 3, 1)
            scatter1 = ax1.scatter(results_df['total_return'], results_df['sharpe'], 
                                  c=results_df['max_drawdown'], s=results_df['total_trades']*5,
                                  cmap='RdYlGn_r', alpha=0.6, edgecolors='black', linewidth=0.5)
            ax1.set_xlabel('Total Return (%)')
            ax1.set_ylabel('Sharpe Ratio')
            ax1.set_title('Sharpe vs Return (size=trades, color=drawdown)')
            plt.colorbar(scatter1, ax=ax1, label='Max Drawdown (%)')
            ax1.grid(True, alpha=0.3)
            
            # 2. Win Rate vs Profit Factor (colored by Sharpe)
            ax2 = plt.subplot(2, 3, 2)
            scatter2 = ax2.scatter(results_df['win_rate'], results_df['profit_factor'],
                                  c=results_df['sharpe'], s=100, cmap='viridis',
                                  alpha=0.6, edgecolors='black', linewidth=0.5)
            ax2.set_xlabel('Win Rate (%)')
            ax2.set_ylabel('Profit Factor')
            ax2.set_title('Win Rate vs Profit Factor (color=Sharpe)')
            plt.colorbar(scatter2, ax=ax2, label='Sharpe Ratio')
            ax2.grid(True, alpha=0.3)
            
            # 3. Distribution of Sharpe Ratios
            ax3 = plt.subplot(2, 3, 3)
            ax3.hist(results_df['sharpe'], bins=20, color='steelblue', alpha=0.7, edgecolor='black')
            ax3.axvline(results_df['sharpe'].mean(), color='red', linestyle='--', 
                       label=f'Mean: {results_df["sharpe"].mean():.2f}')
            ax3.axvline(results_df['sharpe'].median(), color='green', linestyle='--', 
                       label=f'Median: {results_df["sharpe"].median():.2f}')
            ax3.set_xlabel('Sharpe Ratio')
            ax3.set_ylabel('Frequency')
            ax3.set_title('Distribution of Sharpe Ratios')
            ax3.legend()
            ax3.grid(True, alpha=0.3)
            
            # 4. Distribution of Trade Counts
            ax4 = plt.subplot(2, 3, 4)
            ax4.hist(results_df['total_trades'], bins=20, color='coral', alpha=0.7, edgecolor='black')
            ax4.set_xlabel('Total Trades')
            ax4.set_ylabel('Frequency')
            ax4.set_title('Distribution of Trade Counts')
            ax4.grid(True, alpha=0.3)
            
            # 5. Top 10 Combinations by metric
            ax5 = plt.subplot(2, 3, 5)
            top10 = results_df.nlargest(10, metric)
            top10_labels = [f"#{i+1}" for i in range(len(top10))]
            bars = ax5.barh(top10_labels, top10[metric], color='green', alpha=0.7, edgecolor='black')
            ax5.set_xlabel(metric.replace('_', ' ').title())
            ax5.set_title(f'Top 10 Combinations by {metric.replace("_", " ").title()}')
            ax5.invert_yaxis()
            ax5.grid(True, alpha=0.3, axis='x')
            
            # 6. Heatmap of parameter combinations (if exactly 2 params)
            ax6 = plt.subplot(2, 3, 6)
            # Identify parameter columns (exclude metric columns)
            metric_cols = ['combination_id', 'is_valid', 'invalid_reason', 'total_return', 
                          'sharpe', 'sortino', 'calmar', 'max_drawdown', 'win_rate', 
                          'profit_factor', 'total_trades', 'avg_win', 'avg_loss',
                          'volatility', 'stop_loss_type', 'stop_loss_value']
            param_cols = [col for col in results_df.columns if col not in metric_cols]
            
            if len(param_cols) == 2:
                # Create pivot table for heatmap
                pivot = results_df.pivot_table(values=metric, index=param_cols[0], 
                                            columns=param_cols[1], aggfunc='mean')
                sns.heatmap(pivot, annot=True, fmt='.3f', cmap='RdYlGn', ax=ax6, 
                           cbar_kws={'label': metric.replace('_', ' ').title()})
                ax6.set_title(f'{metric.replace("_", " ").title()} Heatmap')
            else:
                ax6.text(0.5, 0.5, f'Heatmap requires\nexactly 2 parameters\n(found {len(param_cols)})', 
                        ha='center', va='center', fontsize=14, transform=ax6.transAxes)
                ax6.set_title(f'{metric.replace("_", " ").title()} Heatmap')
                ax6.axis('off')
            
            plt.tight_layout()
            plt.savefig(filename, dpi=150, bbox_inches='tight')
            
            if show_plots:
                plt.show()
            else:
                plt.close()
            
            if not silent:
                print(f"✓ Optimization chart saved: {filename}")
            
            return filename
            
        except Exception as e:
            if not silent:
                print(f"⚠️ Could not create optimization charts: {e}")
            return None


def create_stoploss_charts(analyzer, filename='stoploss_analysis.png', show_plots=True):
    """Create 4 stop-loss specific charts"""
    r = analyzer.results
    m = analyzer.metrics
    
    if m.get('stoploss_count', 0) == 0:
        print("No stop-loss trades to visualize")
        return
    
    trades_df = pd.DataFrame(r.trades)
    
    if 'exit_reason' not in trades_df.columns:
        print("No exit_reason data available")
        return
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Stop-Loss Analysis', fontsize=16, fontweight='bold', y=0.995)
    
    ax1 = axes[0, 0]
    if m.get('exit_reasons'):
        reasons = pd.Series(m['exit_reasons']).sort_values(ascending=True)
        colors = ['#f44336' if 'stop_loss' in str(r) else '#4CAF50' if r == 'profit_target' else '#2196F3' 
                  for r in reasons.index]
        ax1.barh(range(len(reasons)), reasons.values, color=colors, alpha=0.7, edgecolor='black')
        ax1.set_yticks(range(len(reasons)))
        ax1.set_yticklabels([r.replace('_', ' ').title() for r in reasons.index])
        ax1.set_title('Exit Reasons Distribution', fontsize=12, fontweight='bold')
        ax1.set_xlabel('Number of Trades')
        ax1.grid(True, alpha=0.3, axis='x')
        
        total = sum(reasons.values)
        for i, v in enumerate(reasons.values):
            ax1.text(v, i, f' {(v/total)*100:.1f}%', va='center', fontweight='bold')
    
    ax2 = axes[0, 1]
    sl_trades = trades_df[trades_df['exit_reason'].str.contains('stop_loss', na=False)]
    if len(sl_trades) > 0:
        ax2.hist(sl_trades['pnl'], bins=30, color='#f44336', alpha=0.7, edgecolor='black')
        ax2.axvline(x=0, color='black', linestyle='--', linewidth=2)
        ax2.axvline(x=sl_trades['pnl'].mean(), color='yellow', linestyle='--', linewidth=2, label='Mean')
        ax2.set_title('Stop-Loss P&L Distribution', fontsize=12, fontweight='bold')
        ax2.set_xlabel('P&L ($)')
        ax2.set_ylabel('Frequency')
        ax2.legend()
        ax2.grid(True, alpha=0.3, axis='y')
    
    ax3 = axes[1, 0]
    if len(sl_trades) > 0 and 'entry_date' in sl_trades.columns and 'exit_date' in sl_trades.columns:
        sl_trades_copy = sl_trades.copy()
        sl_trades_copy['entry_date'] = pd.to_datetime(sl_trades_copy['entry_date'])
        sl_trades_copy['exit_date'] = pd.to_datetime(sl_trades_copy['exit_date'])
        sl_trades_copy['days_held'] = (sl_trades_copy['exit_date'] - sl_trades_copy['entry_date']).dt.days
        
        ax3.hist(sl_trades_copy['days_held'], bins=30, color='#FF9800', alpha=0.7, edgecolor='black')
        ax3.axvline(x=sl_trades_copy['days_held'].mean(), color='red', linestyle='--', linewidth=2, label='Mean')
        ax3.set_title('Days Until Stop-Loss Triggered', fontsize=12, fontweight='bold')
        ax3.set_xlabel('Days Held')
        ax3.set_ylabel('Frequency')
        ax3.legend()
        ax3.grid(True, alpha=0.3, axis='y')
    
    ax4 = axes[1, 1]
    if 'stop_type' in sl_trades.columns:
        stop_types = sl_trades['stop_type'].value_counts()
        colors_types = plt.cm.Set3(range(len(stop_types)))
        wedges, texts, autotexts = ax4.pie(stop_types.values, labels=stop_types.index, 
                                            autopct='%1.1f%%', colors=colors_types,
                                            startangle=90)
        for autotext in autotexts:
            autotext.set_color('black')
            autotext.set_fontweight('bold')
        ax4.set_title('Stop-Loss Types', fontsize=12, fontweight='bold')
    else:
        ax4.text(0.5, 0.5, 'No stop_type data', ha='center', va='center', transform=ax4.transAxes)
    
    plt.tight_layout()
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    
    if show_plots:
        plt.show()
    else:
        plt.close()
    
    print(f"Stop-loss charts saved: {filename}")


# ============================================================
# RESULTS EXPORTER (unchanged)
# ============================================================
# ============================================================
# OPTIMAL COLUMN ORDER (150+ columns) - ✅ Added Iron Condor support
# ============================================================
OPTIMAL_COLUMN_ORDER = [
    # 1. IDENTIFIERS (4)
    'entry_date', 'exit_date', 'symbol', 'signal',
    
    # 2. RESULTS (6) - Added type and pnl_pct
    'pnl', 'return_pct', 'exit_reason', 'stop_type',
    'type',  # ✅ BUY_IRON_CONDOR / SELL_IRON_CONDOR
    'pnl_pct',  # ✅ P&L percentage (same as return_pct for compatibility)
    
    # 3. OPTION PARAMETERS (18) - Added Iron Condor strikes
    'strike', 'call_strike', 'put_strike',
    'expiration', 'call_expiration', 'put_expiration',
    'contracts', 'quantity',
    'short_strike', 'long_strike',
    'short_expiration', 'long_expiration',
    'opt_type', 'spread_type',
    # ✅ Iron Condor strikes (4 legs)
    'short_call_strike', 'long_call_strike',
    'short_put_strike', 'long_put_strike',
    
    # 4. POSITION METADATA (12) - ✅ Iron Condor specific
    'dte', 'position_size_pct', 'total_cost', 'strategy_type',
    'capital_at_entry', 'target_allocation', 'actual_allocation',
    'available_equity_at_entry', 'locked_capital_at_entry', 'open_positions_at_entry',
    'highest_price', 'lowest_price',
    
    # 5. ENTRY PRICES (25) - Added Iron Condor 4 legs
    'entry_price', 'underlying_entry_price',
    'call_entry_bid', 'call_entry_ask', 'call_entry_mid',
    'put_entry_bid', 'put_entry_ask', 'put_entry_mid',
    'short_entry_bid', 'short_entry_ask', 'short_entry_mid',
    'long_entry_bid', 'long_entry_ask', 'long_entry_mid',
    # ✅ Iron Condor entry prices (4 legs × 3 prices)
    'short_call_entry_bid', 'short_call_entry_ask', 'short_call_entry_mid',
    'long_call_entry_bid', 'long_call_entry_ask', 'long_call_entry_mid',
    'short_put_entry_bid', 'short_put_entry_ask', 'short_put_entry_mid',
    'long_put_entry_bid', 'long_put_entry_ask', 'long_put_entry_mid',
    
    # 6. ENTRY METRICS (11) - Added Iron Condor IV
    'entry_z_score', 'entry_lean', 'iv_lean_entry',
    'call_iv_entry', 'put_iv_entry', 'iv_entry',
    'iv_rank_entry', 'iv_percentile_entry',
    # ✅ Iron Condor entry IV (4 legs)
    'short_call_iv_entry', 'long_call_iv_entry',
    'short_put_iv_entry', 'long_put_iv_entry',
    
    # 7. ENTRY GREEKS (28) - Added Iron Condor Greeks
    'call_delta_entry', 'call_gamma_entry', 'call_vega_entry', 'call_theta_entry',
    'put_delta_entry', 'put_gamma_entry', 'put_vega_entry', 'put_theta_entry',
    'net_delta_entry', 'net_gamma_entry', 'net_vega_entry', 'net_theta_entry',
    # ✅ Iron Condor entry Greeks (4 legs × 4 greeks)
    'short_call_delta_entry', 'short_call_gamma_entry', 'short_call_vega_entry', 'short_call_theta_entry',
    'long_call_delta_entry', 'long_call_gamma_entry', 'long_call_vega_entry', 'long_call_theta_entry',
    'short_put_delta_entry', 'short_put_gamma_entry', 'short_put_vega_entry', 'short_put_theta_entry',
    'long_put_delta_entry', 'long_put_gamma_entry', 'long_put_vega_entry', 'long_put_theta_entry',
    
    # 8. ENTRY CRITERIA (20) - Added Iron Condor signals & Earnings data
    'target_delta_entry', 'delta_threshold_entry',
    'entry_price_pct', 'distance_from_strike_entry',
    'dte_entry', 'target_dte_entry',
    'volume_entry', 'open_interest_entry', 'volume_ratio_entry',
    'entry_criteria', 'entry_signal', 'entry_reason',
    # ✅ Iron Condor strategy signals
    'entry_iv_rank', 'entry_signal_type', 'entry_wing_width',
    # ✅ Earnings Momentum strategy data
    'entry_earnings_date', 'entry_earnings_surprise_pct', 'entry_earnings_estimate',
    'entry_earnings_reported', 'entry_earnings_direction',
    
    # 9. STOP-LOSS (2)
    'stop_threshold', 'actual_value',
    
    # 10. EXIT PRICES (19) - Added Iron Condor 4 legs
    'exit_price', 'underlying_exit_price', 'underlying_change_pct',
    'call_exit_bid', 'call_exit_ask',
    'put_exit_bid', 'put_exit_ask',
            'short_exit_bid', 'short_exit_ask',
            'long_exit_bid', 'long_exit_ask',
    # ✅ Iron Condor exit prices (4 legs × 2 prices)
    'short_call_exit_bid', 'short_call_exit_ask',
    'long_call_exit_bid', 'long_call_exit_ask',
    'short_put_exit_bid', 'short_put_exit_ask',
    'long_put_exit_bid', 'long_put_exit_ask',
    
    # 11. EXIT METRICS (12) - Added Iron Condor IV
    'exit_z_score', 'exit_lean', 'iv_lean_exit',
    'call_iv_exit', 'put_iv_exit', 'iv_exit',
    'iv_rank_exit', 'iv_percentile_exit',
    # ✅ Iron Condor exit IV (4 legs)
    'short_call_iv_exit', 'long_call_iv_exit',
    'short_put_iv_exit', 'long_put_iv_exit',
    
    # 12. EXIT GREEKS (28) - Added Iron Condor Greeks
    'call_delta_exit', 'call_gamma_exit', 'call_vega_exit', 'call_theta_exit',
    'put_delta_exit', 'put_gamma_exit', 'put_vega_exit', 'put_theta_exit',
    'net_delta_exit', 'net_gamma_exit', 'net_vega_exit', 'net_theta_exit',
    # ✅ Iron Condor exit Greeks (4 legs × 4 greeks)
    'short_call_delta_exit', 'short_call_gamma_exit', 'short_call_vega_exit', 'short_call_theta_exit',
    'long_call_delta_exit', 'long_call_gamma_exit', 'long_call_vega_exit', 'long_call_theta_exit',
    'short_put_delta_exit', 'short_put_gamma_exit', 'short_put_vega_exit', 'short_put_theta_exit',
    'long_put_delta_exit', 'long_put_gamma_exit', 'long_put_vega_exit', 'long_put_theta_exit',
    
    # 13. EXIT CRITERIA (11)
    'target_delta_exit', 'delta_threshold_exit',
    'exit_price_pct', 'distance_from_strike_exit',
    'dte_exit', 'target_dte_exit',
    'volume_exit', 'open_interest_exit', 'volume_ratio_exit',
    'exit_criteria', 'exit_signal',
    
    # 14. INTRADAY DATA (18)
    'stock_intraday_high', 'stock_intraday_low', 'stock_intraday_close',
    'stock_stop_trigger_time', 'stock_stop_trigger_price',
    'stock_stop_trigger_bid', 'stock_stop_trigger_ask', 'stock_stop_trigger_last',
    'intraday_data_points', 'intraday_data_available', 'stop_triggered_by',
    'breach_direction', 'stop_level_high', 'stop_level_low',
    'intraday_bar_index', 'intraday_volume',
    'intraday_trigger_bid_time', 'intraday_trigger_ask_time',
    
    # 15. ADDITIONAL FIELDS (for compatibility)
    'is_short_bias',
    'underlying_price',  # ✅ Final underlying price
]


def reorder_columns(df, column_order=OPTIMAL_COLUMN_ORDER):
    """
    Reorder DataFrame columns according to optimal order.
    
    Args:
        df: DataFrame to reorder
        column_order: List of column names in desired order (default: OPTIMAL_COLUMN_ORDER)
    
    Returns:
        DataFrame with reordered columns
    """
    # Get columns that exist in the DataFrame and are in the optimal order
    ordered_columns = [col for col in column_order if col in df.columns]
    
    # Add any remaining columns that weren't in the optimal order (at the end)
    remaining_columns = [col for col in df.columns if col not in ordered_columns]
    
    # Combine ordered + remaining
    final_order = ordered_columns + remaining_columns
    
    return df[final_order]


# ============================================================
# NOTE: STRATEGY_PARAMS_MAP has been migrated to STRATEGIES dict
# (see top of file for unified STRATEGIES registry)
# ============================================================


def detect_strategy_type(config):
    """
    Detect strategy type based on signature parameters in config.
    (Data-driven: reads from STRATEGIES registry)
    
    Args:
        config: Strategy config dictionary
        
    Returns:
        Strategy type string or None if not detected
    """
    # Check lowercase variants first (for backwards compatibility)
    for lower_name, upper_name in _STRATEGY_NAME_MAP.items():
        strategy = STRATEGIES.get(upper_name)
        if strategy and 'file_naming' in strategy:
            signature = strategy['file_naming']['signature']
            if all(param in config for param in signature):
                return lower_name  # Return lowercase for file naming
    return None


def format_params_string(config):
    """
    Generate compact parameter string from config for file naming.
    (Data-driven: reads from STRATEGIES registry)
    
    Supports:
    - Custom formatter via 'params_formatter' in config
    - Automatic strategy detection and formatting via STRATEGIES
    - Fallback to "default" if strategy not detected
    
    Format examples:
    - IV Lean: Z2.0_E0.03_L45_DT30_0.3_SL4
    - Iron Condor: WW5_BW10_DT45_PT50_0.3_SL100
    - Credit Spread: SW5_D30_DT45_PT50_0.3
    
    Args:
        config: Strategy config dictionary
        
    Returns:
        Formatted parameter string
    """
    # ═══════════════════════════════════════════════════════════════════════
    # 1. CHECK FOR CUSTOM FORMATTER (highest priority)
    # ═══════════════════════════════════════════════════════════════════════
    if 'params_formatter' in config:
        try:
            custom_result = config['params_formatter'](config)
            if custom_result:
                return custom_result
        except Exception as e:
            print(f"[WARNING] Custom params_formatter failed: {e}")
            # Fall through to automatic detection
    
    # ═══════════════════════════════════════════════════════════════════════
    # 2. AUTOMATIC STRATEGY DETECTION (from STRATEGIES registry)
    # ═══════════════════════════════════════════════════════════════════════
    # First try signature-based detection
    strategy_type_lower = detect_strategy_type(config)
    
    # ✅ Fallback: Use explicit strategy_type from config if detection failed
    if not strategy_type_lower and config.get('strategy_type'):
        strategy_type_lower = config['strategy_type'].lower()
    
    # Debug: Show detection result
    if config.get('debuginfo', 0) >= 2:
        print(f"[DEBUG format_params_string] Detected strategy: {strategy_type_lower}")
        print(f"[DEBUG format_params_string] Config keys: {list(config.keys())[:10]}...")
    
    if strategy_type_lower:
        # Convert to uppercase and get from STRATEGIES
        strategy_type_upper = _STRATEGY_NAME_MAP.get(strategy_type_lower, strategy_type_lower.upper())
        strategy = STRATEGIES.get(strategy_type_upper)
        
        if strategy and 'file_naming' in strategy:
            parts = []
            
            # ✅ Auto-calculate lookback_period if missing but lookback_ratio exists
            if 'lookback_period' not in config and 'lookback_ratio' in config:
                try:
                    config['lookback_period'] = auto_calculate_lookback_period(config, indicator_name='default')
                except Exception as e:
                    pass  # Will be handled below
            
            # ✅ Helper: Get value from config OR nested configs (earnings_config, stop_loss_config)
            def get_param_value(key):
                """Get parameter value from config, earnings_config, or stop_loss_config"""
                if key in config:
                    return config[key]
                # Check earnings_config
                earnings_cfg = config.get('earnings_config', {})
                if key in earnings_cfg:
                    return earnings_cfg[key]
                # Check stop_loss_config
                sl_cfg = config.get('stop_loss_config', {})
                if key in sl_cfg:
                    return sl_cfg[key]
                if key == 'stop_loss_pct' and 'value' in sl_cfg:
                    return sl_cfg['value']
                return None
            
            # Format strategy-specific parameters
            for param_def in strategy['file_naming']['format']:
                key = param_def['key']
                code = param_def['code']
                format_func = param_def['formatter']
                
                value = get_param_value(key)
                if value is not None:
                    try:
                        formatted = format_func(value)
                        if code:
                            parts.append(f"{code}{formatted}")
                        else:
                            parts.append(formatted)
                    except Exception as e:
                        print(f"[WARNING] Failed to format {key}: {e}")
                # Debug: Show missing keys
                elif config.get('debuginfo', 0) >= 2:
                    print(f"[DEBUG format_params_string] Missing key '{key}' in config for strategy {strategy_type_upper}")
            
            # ═══════════════════════════════════════════════════════════════════
            # AUTO-FORMAT EARNINGS PARAMS (if earnings_config exists)
            # ═══════════════════════════════════════════════════════════════════
            earnings_cfg = config.get('earnings_config', {})
            if earnings_cfg.get('mode') in ['trade_around', 'avoid']:
                earnings_formats = [
                    ('entry_days_before', 'ED', lambda x: f"{int(x)}"),
                    ('exit_days_after', 'XD', lambda x: f"{int(x)}"),
                    ('iv_percentile_min', 'IV', lambda x: f"{int(x)}" if x else None),
                    ('min_implied_move', 'IM', lambda x: f"{int(x*100)}" if x else None),
                ]
                for key, code, fmt in earnings_formats:
                    # Check both root config and earnings_config
                    value = config.get(key) or earnings_cfg.get(key)
                    if value is not None:
                        try:
                            formatted = fmt(value)
                            if formatted and code:
                                parts.append(f"{code}{formatted}")
                        except:
                            pass
        
        # Add stop-loss (if enabled)
        if config.get('stop_loss_enabled') and 'stop_loss_config' in config:
            sl_config = config['stop_loss_config']
            sl_value = sl_config.get('value', 0)
            sl_type = sl_config.get('type', 'none')
            
            if sl_type == 'combined':
                # Combined Stop-Loss: format as PL{value}_DIR{value}_{logic}
                combined_settings = sl_config.get('combined_settings', {})
                pl_loss = combined_settings.get('pl_loss', 0)
                directional = combined_settings.get('directional', 0)
                logic = combined_settings.get('logic', 'or').upper()
                
                if pl_loss > 0 or directional > 0:
                    parts.append(f"PL{int(pl_loss*100)}_DIR{int(directional*100)}_{logic}")
            elif sl_type != 'none' and sl_value > 0:
                if sl_type in ['directional', 'pl_loss', 'fixed_pct']:
                    parts.append(f"SL{int(sl_value*100)}")
        
        return "_".join(parts) if parts else "default"
    
    # ═══════════════════════════════════════════════════════════════════════
    # 3. FALLBACK TO "default"
    # ═══════════════════════════════════════════════════════════════════════
    return "default"


class ResultsExporter:
    """Export backtest results to multiple file formats (CSV, TXT, JSON)"""
    
    @staticmethod
    def export_all(analyzer, prefix='backtest', silent=False, mode=None, config_name=None):
        """
        Export backtest results with automatic folder creation based on mode.
        
        Args:
            analyzer (BacktestAnalyzer): Analyzer instance with calculated metrics
            prefix (str): Filename prefix WITHOUT path if mode specified, or full path if mode=None
            silent (bool): If True, suppress print output
            mode (str): Run mode - 'SINGLE', 'BASELINE', 'COMPARISON', 'OPTIMIZATION', or None
                       If None, uses prefix as-is (backward compatible)
                       If specified, creates timestamped folder automatically
            config_name (str): Configuration name for COMPARISON mode (e.g., 'SL5_directional')
        
        Returns:
            dict with keys:
                'files': list of tuples [(filepath, description), ...]
                'folder': str path to results folder
                
            Example:
                {
                    'files': [
                        ('single_backtest_results/20251113_080000/backtest_Z2.0_trades.csv', '(69 columns)'),
                        ('single_backtest_results/20251113_080000/backtest_Z2.0_equity.csv', ''),
                        ...
                    ],
                    'folder': 'single_backtest_results/20251113_080000'
                }
        
        Note:
            If mode=None (legacy behavior), returns just the list for backward compatibility.
        """
        import os
        from pathlib import Path
        from datetime import datetime
        
        # Auto-create folder structure based on mode
        results_folder = None
        if mode is not None:
            mode_upper = mode.upper()
            
            # Determine base folder name
            folder_map = {
                'SINGLE': 'single_backtest_results',
                'BASELINE': 'baseline_results',
                'COMPARISON': 'comparison_results',
                'OPTIMIZATION': 'optimization_results'
            }
            
            base_folder = folder_map.get(mode_upper, 'backtest_results')
            
            # Create timestamped folder
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            results_folder = Path(base_folder) / timestamp
            
            # For COMPARISON mode, create subfolder for specific config
            if mode_upper == 'COMPARISON' and config_name:
                results_folder = results_folder / config_name.replace(' ', '_')
            
            results_folder.mkdir(parents=True, exist_ok=True)
            results_folder = str(results_folder)
            
            # Update prefix to include folder path
            params_str = format_params_string(analyzer.results.config)
            
            if mode_upper == 'BASELINE':
                file_prefix = f"baseline_{params_str}"
            elif mode_upper == 'COMPARISON' and config_name:
                file_prefix = f"{config_name.replace(' ', '_')}_{params_str}"
            else:
                file_prefix = f"{prefix}_{params_str}" if params_str != "default" else prefix
            
            prefix = os.path.join(results_folder, file_prefix)
            
            if not silent:
                print(f"📁 Created results folder: {results_folder}")
        
        # Original export logic continues...
        r = analyzer.results
        m = analyzer.metrics
        
        if len(r.trades) == 0:
            if not silent:
                print("No trades to export")
            return []
        
        trades_df = pd.DataFrame(r.trades)
        
        # Format dates
        trades_df['entry_date'] = pd.to_datetime(trades_df['entry_date']).dt.strftime('%Y-%m-%d')
        trades_df['exit_date'] = pd.to_datetime(trades_df['exit_date']).dt.strftime('%Y-%m-%d')
        
        # Reorder columns using optimal order
        trades_df = reorder_columns(trades_df)
        
        # Round numeric columns to 2 decimals
        numeric_columns = trades_df.select_dtypes(include=['float64', 'float32', 'float']).columns
        for col in numeric_columns:
            trades_df[col] = trades_df[col].round(5)
        
        exported_files = []
        
        # ========================================================
        # VALIDATION: Check CSV columns against expected structure
        # ========================================================
        if not silent and len(r.trades) > 0:
            # Try to detect strategy type
            strategy_type = r.config.get('strategy_type', '')
            if not strategy_type:
                # Try to extract from strategy_name
                strategy_name = r.config.get('strategy_name', '')
                name_upper = strategy_name.upper()
                if 'IRON CONDOR' in name_upper or 'IRON_CONDOR' in name_upper:
                    strategy_type = 'IRON_CONDOR'
                elif 'STRADDLE' in name_upper and 'Z-SCORE' not in name_upper and 'IV LEAN' not in name_upper:
                    strategy_type = 'STRADDLE'
                elif 'STRANGLE' in name_upper:
                    strategy_type = 'STRANGLE'
                elif 'IV LEAN' in name_upper or 'Z-SCORE' in name_upper:
                    strategy_type = 'IV_LEAN'
                elif 'CREDIT SPREAD' in name_upper:
                    strategy_type = 'CREDIT_SPREAD'
                elif 'DEBIT SPREAD' in name_upper:
                    strategy_type = 'DEBIT_SPREAD'
                elif 'BUTTERFLY' in name_upper and 'IRON' not in name_upper:
                    strategy_type = 'BUTTERFLY'
                elif 'IRON BUTTERFLY' in name_upper or 'IRON_BUTTERFLY' in name_upper:
                    strategy_type = 'IRON_BUTTERFLY'
                elif 'CALENDAR' in name_upper:
                    strategy_type = 'CALENDAR_SPREAD'
                elif 'DIAGONAL' in name_upper:
                    strategy_type = 'DIAGONAL_SPREAD'
                elif 'COVERED CALL' in name_upper or 'COVERED_CALL' in name_upper:
                    strategy_type = 'COVERED_CALL'
            
            # Validate if strategy type detected
            if strategy_type:
                expected_cols = StrategyRegistry.get_expected_csv_columns(strategy_type)
                actual_cols = set(trades_df.columns)
                
                # Check for leg-specific fields (exit data)
                leg_fields_missing = []
                leg_fields_present = []
                for col in expected_cols:
                    if '_exit_' in col or '_iv_exit' in col:
                        if col in actual_cols:
                            leg_fields_present.append(col)
                        else:
                            leg_fields_missing.append(col)
                
                # Only warn if leg fields are completely missing (not just some missing)
                # Some fields may be missing legitimately (e.g., stop_threshold if no stop-loss)
                if leg_fields_missing and not leg_fields_present:
                    print(f"\n⚠️  WARNING: Strategy '{strategy_type}' - no leg-specific exit data found in CSV")
                    print(f"   Expected fields like: {leg_fields_missing[:3]}...")
                    print(f"   This may indicate missing data in close_position() kwargs")
        
        trades_df.to_csv(f'{prefix}_trades.csv', index=False)
        exported_files.append((f'{prefix}_trades.csv', f"({len(trades_df.columns)} columns)"))
        if not silent:
            print(f"Exported: {prefix}_trades.csv ({len(trades_df.columns)} columns)")
        
        equity_df = pd.DataFrame({
            'date': pd.to_datetime(r.equity_dates).strftime('%Y-%m-%d'),
            'equity': r.equity_curve
        })
        equity_df['equity'] = equity_df['equity'].round(5)
        equity_df.to_csv(f'{prefix}_equity.csv', index=False)
        exported_files.append((f'{prefix}_equity.csv', ""))
        if not silent:
            print(f"Exported: {prefix}_equity.csv")
        
        with open(f'{prefix}_summary.txt', 'w') as f:
            f.write("BACKTEST SUMMARY\n")
            f.write("="*70 + "\n\n")
            f.write(f"Strategy: {r.config.get('strategy_name', 'Unknown')}\n")
            f.write(f"Period: {r.config.get('start_date')} to {r.config.get('end_date')}\n")
            f.write(f"Symbol: {r.config.get('symbol', 'N/A')}\n\n")
            
            # STRATEGY PARAMETERS (✅ Data-driven from STRATEGIES)
            f.write("STRATEGY PARAMETERS\n")
            f.write("-"*70 + "\n")
            
            # Try to get strategy from registry (smart detection)
            strategy_type = r.config.get('strategy_type', '')
            if not strategy_type:
                # Try to extract from strategy_name
                strategy_name = r.config.get('strategy_name', '')
                # Map common names to strategy types
                name_upper = strategy_name.upper()
                if 'IRON CONDOR' in name_upper or 'IRON_CONDOR' in name_upper:
                    strategy_type = 'IRON_CONDOR'
                elif 'IV LEAN' in name_upper or 'Z-SCORE' in name_upper:
                    strategy_type = 'IV_LEAN'
                elif 'STRADDLE' in name_upper:
                    strategy_type = 'STRADDLE'
                elif 'STRANGLE' in name_upper:
                    strategy_type = 'STRANGLE'
                elif 'BUTTERFLY' in name_upper:
                    strategy_type = 'BUTTERFLY' if 'IRON' not in name_upper else 'IRON_BUTTERFLY'
                elif 'CALENDAR' in name_upper:
                    strategy_type = 'CALENDAR_SPREAD'
                elif 'DIAGONAL' in name_upper:
                    strategy_type = 'DIAGONAL_SPREAD'
                elif 'COVERED' in name_upper:
                    strategy_type = 'COVERED_CALL'
                elif 'BULL PUT' in name_upper:
                    strategy_type = 'BULL_PUT_SPREAD'
                elif 'BEAR CALL' in name_upper:
                    strategy_type = 'BEAR_CALL_SPREAD'
                elif 'BULL CALL' in name_upper:
                    strategy_type = 'BULL_CALL_SPREAD'
                elif 'BEAR PUT' in name_upper:
                    strategy_type = 'BEAR_PUT_SPREAD'
                elif 'CREDIT' in name_upper and 'SPREAD' in name_upper:
                    strategy_type = 'CREDIT_SPREAD'
                elif 'DEBIT' in name_upper and 'SPREAD' in name_upper:
                    strategy_type = 'DEBIT_SPREAD'
                else:
                    strategy_type = strategy_name.upper().replace(' ', '_').replace('-', '_')
            
            strategy = StrategyRegistry.get(strategy_type)
            
            if strategy and 'config_params' in strategy:
                # ✅ Use config_params from STRATEGIES (data-driven!)
                for param in strategy['config_params']:
                    if param.get('in_summary', True):
                        key = param['key']
                        if key in r.config:
                            label = param['label']
                            format_str = param['format']
                            value = r.config[key]
                            try:
                                formatted = format_str.format(value)
                                f.write(f"{label}: {formatted}\n")
                            except:
                                f.write(f"{label}: {value}\n")
            else:
                # Fallback: legacy logic for unknown strategies
                if 'z_score_entry' in r.config:
                    f.write(f"Z-Score Entry: {r.config['z_score_entry']:.1f}\n")
                if 'z_score_exit' in r.config:
                    f.write(f"Exit Threshold: {r.config['z_score_exit']:.2f}\n")
                if 'lookback_period' in r.config:
                    f.write(f"Lookback Period: {r.config['lookback_period']} days\n")
                if 'dte_target' in r.config:
                    f.write(f"DTE Target: {r.config['dte_target']} days\n")
                if 'position_size_pct' in r.config:
                    f.write(f"Position Size: {r.config['position_size_pct']*100:.1f}% of capital\n")
            
            # Stop-loss parameters
            if r.config.get('stop_loss_enabled'):
                f.write(f"\nStop-Loss: ENABLED\n")
                sl_config = r.config.get('stop_loss_config', {})
                sl_type = sl_config.get('type', 'unknown')
                sl_value = sl_config.get('value', 0)
                
                if sl_type == 'directional':
                    f.write(f"  Type: Directional (underlying movement)\n")
                    f.write(f"  Threshold: {sl_value*100:.1f}%\n")
                elif sl_type == 'pl_loss':
                    f.write(f"  Type: P&L Loss\n")
                    f.write(f"  Threshold: {sl_value*100:.1f}%\n")
                elif sl_type == 'fixed_pct':
                    f.write(f"  Type: Fixed Percentage\n")
                    f.write(f"  Threshold: {sl_value*100:.1f}%\n")
                elif sl_type == 'trailing':
                    f.write(f"  Type: Trailing\n")
                    f.write(f"  Threshold: {sl_value*100:.1f}%\n")
                elif sl_type == 'time_based':
                    f.write(f"  Type: Time-based\n")
                    f.write(f"  Max Days: {sl_value}\n")
                elif sl_type == 'combined':
                    f.write(f"  Type: Combined (P&L + Directional)\n")
                    f.write(f"  P&L Threshold: {sl_config.get('pl_loss_value', 0)*100:.1f}%\n")
                    f.write(f"  Directional Threshold: {sl_config.get('directional_value', 0)*100:.1f}%\n")
            else:
                f.write(f"\nStop-Loss: DISABLED\n")
            
            f.write("\n")
            
            # PERFORMANCE
            f.write("PERFORMANCE\n")
            f.write("-"*70 + "\n")
            f.write(f"Total Return: {m['total_return']:.2f}%\n")
            f.write(f"Sharpe: {m['sharpe']:.2f}\n")
            f.write(f"Max DD: {m['max_drawdown']:.2f}%\n")
            f.write(f"Trades: {m['total_trades']}\n")
        
        exported_files.append((f'{prefix}_summary.txt', ""))
        if not silent:
            print(f"Exported: {prefix}_summary.txt")
        
        # Export metrics as JSON with rounded values and config
        import json
        import numpy as np
        
        # Helper function to convert values to JSON-serializable types
        def convert_value(value):
            if isinstance(value, (np.integer, np.floating)):
                value = value.item()
            if isinstance(value, float):
                return round(value, 5)
            elif isinstance(value, (int, str, bool, type(None))):
                return value
            elif isinstance(value, dict):
                return {k: convert_value(v) for k, v in value.items()}
            else:
                return str(value)  # Fallback for other types
        
        # Build JSON structure with config and metrics
        export_data = {
            "strategy_info": {
                "name": r.config.get('strategy_name', 'Unknown'),
                "symbol": r.config.get('symbol', 'N/A'),
                "start_date": r.config.get('start_date', ''),
                "end_date": r.config.get('end_date', ''),
            },
            "strategy_parameters": {},
            "performance_metrics": {}
        }
        
        # Add strategy parameters
        if 'z_score_entry' in r.config:
            export_data["strategy_parameters"]["z_score_entry"] = convert_value(r.config['z_score_entry'])
        if 'z_score_exit' in r.config:
            export_data["strategy_parameters"]["exit_threshold"] = convert_value(r.config['z_score_exit'])
        if 'lookback_period' in r.config:
            export_data["strategy_parameters"]["lookback_period_days"] = convert_value(r.config['lookback_period'])
        if 'dte_target' in r.config:
            export_data["strategy_parameters"]["dte_target_days"] = convert_value(r.config['dte_target'])
        if 'position_size_pct' in r.config:
            export_data["strategy_parameters"]["position_size_pct"] = convert_value(r.config['position_size_pct'])
        
        # Add stop-loss info
        if r.config.get('stop_loss_enabled'):
            sl_config = r.config.get('stop_loss_config', {})
            export_data["strategy_parameters"]["stop_loss"] = {
                "enabled": True,
                "type": sl_config.get('type', 'unknown'),
                "value": convert_value(sl_config.get('value', 0))
            }
            if sl_config.get('type') == 'combined':
                export_data["strategy_parameters"]["stop_loss"]["pl_loss_value"] = convert_value(sl_config.get('pl_loss_value', 0))
                export_data["strategy_parameters"]["stop_loss"]["directional_value"] = convert_value(sl_config.get('directional_value', 0))
        else:
            export_data["strategy_parameters"]["stop_loss"] = {"enabled": False}
        
        # Add performance metrics
        for key, value in m.items():
            export_data["performance_metrics"][key] = convert_value(value)
        
        with open(f'{prefix}_metrics.json', 'w') as f:
            json.dump(export_data, f, indent=2)
        
        exported_files.append((f'{prefix}_metrics.json', ""))
        if not silent:
            print(f"Exported: {prefix}_metrics.json")
        
        # Return format depends on whether mode was specified
        if mode is not None and results_folder is not None:
            return {
                'files': exported_files,
                'folder': results_folder
            }
        else:
            # Legacy behavior for backward compatibility
            return exported_files


# ============================================================
# RUN BACKTEST (unchanged)
# ============================================================
def run_backtest(strategy_function, config, print_report=True,
                 create_charts=True, export_results=True,
                 chart_filename='backtest_results.png',
                 export_prefix='backtest',
                 progress_context=None):
    """Run complete backtest"""
    
    # Check if running inside optimization
    is_optimization = progress_context and progress_context.get('is_optimization', False)
    
    if not progress_context and not is_optimization:
        print("="*80)
        print(" "*25 + "STARTING BACKTEST")
        print("="*80)
        print(f"Strategy: {config.get('strategy_name', 'Unknown')}")
        print(f"Period: {config.get('start_date')} to {config.get('end_date')}")
        print(f"Capital: ${config.get('initial_capital', 0):,.0f}")
        print("="*80 + "\n")
    
    if progress_context:
        config['_progress_context'] = progress_context
    
    results = strategy_function(config)
    
    if '_progress_context' in config:
        del config['_progress_context']
    
    if not is_optimization:
        print("\n[*] Calculating metrics...")
    analyzer = BacktestAnalyzer(results)
    analyzer.calculate_all_metrics()
    
    if print_report:
        print("\n" + "="*80)
        ResultsReporter.print_full_report(analyzer)
    
    # Store file info for later printing (in optimization mode)
    analyzer.chart_file = None
    analyzer.exported_files = []
    
    # Export charts during optimization if requested
    if create_charts and len(results.trades) > 0:
        # Auto-generate chart filename with parameters if using default
        actual_chart_filename = chart_filename
        if chart_filename == 'backtest_results.png' and not is_optimization:
            params_str = format_params_string(config)
            actual_chart_filename = f'backtest_{params_str}_chart.png'
        
        if not is_optimization:
            print(f"\n[*] Creating charts: {actual_chart_filename}")
        try:
            # Don't show plots during optimization, just save them
            chart_file = ChartGenerator.create_all_charts(
                analyzer, actual_chart_filename, 
                show_plots=not is_optimization,
                silent=is_optimization  # ← Silent in optimization
            )
            analyzer.chart_file = chart_file
        except Exception as e:
            if not is_optimization:
                print(f"[ERROR] Charts failed: {e}")
    
    # Export results during optimization if requested
    if export_results and len(results.trades) > 0:
        # Auto-generate prefix with parameters if using default
        actual_prefix = export_prefix
        if export_prefix == 'backtest' and not is_optimization:
            params_str = format_params_string(config)
            actual_prefix = f'backtest_{params_str}'
        
        if not is_optimization:
            print(f"\n[*] Exporting: {actual_prefix}_*")
        try:
            exported = ResultsExporter.export_all(
                analyzer, actual_prefix,
                silent=is_optimization  # ← Silent in optimization
            )
            analyzer.exported_files = exported
        except Exception as e:
            if not is_optimization:
                print(f"[ERROR] Export failed: {e}")
    
    return analyzer


def run_backtest_with_stoploss(strategy_function, config, print_report=True,
                               create_charts=True, export_results=True,
                               chart_filename='backtest_results.png',
                               export_prefix='backtest',
                               create_stoploss_report=True,
                               create_stoploss_charts=True,
                               progress_context=None):
    """Enhanced run_backtest with stop-loss analysis"""
    
    analyzer = run_backtest(
        strategy_function, config,
        print_report=False,
        create_charts=create_charts,
        export_results=export_results,
        chart_filename=chart_filename,
        export_prefix=export_prefix,
        progress_context=progress_context
    )
    
    calculate_stoploss_metrics(analyzer)
    
    if print_report:
        print("\n" + "="*80)
        ResultsReporter.print_full_report(analyzer)
        
        if create_stoploss_report and analyzer.metrics.get('stoploss_count', 0) > 0:
            print_stoploss_section(analyzer)
    
    if create_stoploss_charts and analyzer.metrics.get('stoploss_count', 0) > 0:
        print(f"\n[*] Creating stop-loss analysis charts...")
        try:
            stoploss_chart_name = chart_filename.replace('.png', '_stoploss.png') if chart_filename else 'stoploss_analysis.png'
            create_stoploss_charts(analyzer, stoploss_chart_name)
        except Exception as e:
            print(f"[ERROR] Stop-loss charts failed: {e}")
    
    return analyzer


# ============================================================
# STOP-LOSS CONFIG (ENHANCED WITH COMBINED)
# ============================================================
class StopLossConfig:
    """
    Universal stop-loss configuration builder (ENHANCED)
    
    NEW METHOD:
    - combined(): Requires BOTH pl_loss AND directional conditions
    
    IMPORTANT:
    - directional(): Creates EOD directional stop (checked once per day)
    - For INTRADAY directional stops, use INTRADAY_STOPS_CONFIG (separate system)
    """
    
    @staticmethod
    def _normalize_pct(value):
        """Convert any number to decimal (0.30)"""
        if value >= 1:
            return value / 100
        return value
    
    @staticmethod
    def _format_pct(value):
        """Format percentage for display"""
        if value >= 1:
            return f"{value:.0f}%"
        return f"{value*100:.0f}%"
    
    @staticmethod
    def none():
        """No stop-loss"""
        return {
            'enabled': False,
            'type': 'none',
            'value': 0,
            'name': 'No Stop-Loss',
            'description': 'No stop-loss protection'
        }
    
    @staticmethod
    def fixed(pct):
        """Fixed percentage stop-loss"""
        decimal = StopLossConfig._normalize_pct(pct)
        display = StopLossConfig._format_pct(pct)
        
        return {
            'enabled': True,
            'type': 'fixed_pct',
            'value': decimal,
            'name': f'Fixed {display}',
            'description': f'Fixed stop at {display} loss'
        }
    
    @staticmethod
    def trailing(pct, trailing_distance=None):
        """Trailing stop-loss"""
        decimal = StopLossConfig._normalize_pct(pct)
        display = StopLossConfig._format_pct(pct)
        
        config = {
            'enabled': True,
            'type': 'trailing',
            'value': decimal,
            'name': f'Trailing {display}',
            'description': f'Trailing stop at {display} from peak'
        }
        
        if trailing_distance is not None:
            config['trailing_distance'] = StopLossConfig._normalize_pct(trailing_distance)
        
        return config
    
    @staticmethod
    def time_based(days):
        """Time-based stop"""
        return {
            'enabled': True,
            'type': 'time_based',
            'value': days,
            'name': f'Time {days}d',
            'description': f'Exit after {days} days'
        }
    
    @staticmethod
    def volatility(atr_multiplier):
        """ATR-based stop"""
        return {
            'enabled': True,
            'type': 'volatility',
            'value': atr_multiplier,
            'name': f'ATR {atr_multiplier:.1f}x',
            'description': f'Stop at {atr_multiplier:.1f}× ATR',
            'requires_atr': True
        }
    
    @staticmethod
    def pl_loss(pct):
        """P&L-based stop using real bid/ask prices"""
        decimal = StopLossConfig._normalize_pct(pct)
        display = StopLossConfig._format_pct(pct)
        
        return {
            'enabled': True,
            'type': 'pl_loss',
            'value': decimal,
            'name': f'P&L Loss {display}',
            'description': f'Stop when P&L drops to -{display}'
        }
    
    @staticmethod
    def directional(pct):
        """EOD directional stop based on underlying movement (checked once per day)"""
        decimal = StopLossConfig._normalize_pct(pct)
        display = StopLossConfig._format_pct(pct)
        
        return {
            'enabled': True,
            'type': 'directional',
            'value': decimal,
            'name': f'EOD Directional {display}',
            'description': f'Stop when underlying moves {display} (checked at EOD)'
        }
    
    # ========================================================
    # NEW: COMBINED STOP (REQUIRES BOTH CONDITIONS)
    # ========================================================
    
    @staticmethod
    def combined(pl_loss_pct, directional_pct):
        """
        Combined stop: Requires BOTH conditions (from code 2)
        
        Args:
            pl_loss_pct: P&L loss threshold (e.g., 5 or 0.05 = -5%)
            directional_pct: Underlying move threshold (e.g., 3 or 0.03 = 3%)
        
        Example:
            StopLossConfig.combined(5, 3)
            # Triggers only when BOTH:
            # 1. P&L drops to -5%
            # 2. Underlying moves 3% adversely
        """
        pl_decimal = StopLossConfig._normalize_pct(pl_loss_pct)
        dir_decimal = StopLossConfig._normalize_pct(directional_pct)
        
        pl_display = StopLossConfig._format_pct(pl_loss_pct)
        dir_display = StopLossConfig._format_pct(directional_pct)
        
        return {
            'enabled': True,
            'type': 'combined',
            'value': {
                'pl_loss': pl_decimal,
                'directional': dir_decimal
            },
            'name': f'Combined (P&L {pl_display} + Dir {dir_display})',
            'description': f'Stop when P&L<-{pl_display} AND underlying moves {dir_display}'
        }
    
    # ========================================================
    # BACKWARD COMPATIBILITY
    # ========================================================
    
    @staticmethod
    def time(days):
        """Alias for time_based()"""
        return StopLossConfig.time_based(days)
    
    @staticmethod
    def atr(multiplier):
        """Alias for volatility()"""
        return StopLossConfig.volatility(multiplier)
    
    # ========================================================
    # PRESETS (WITH COMBINED STOPS)
    # ========================================================
    
    @staticmethod
    def presets():
        """Generate all standard stop-loss presets (UPDATED WITH COMBINED)"""
        return {
            'none': StopLossConfig.none(),
            
            'fixed_20': StopLossConfig.fixed(20),
            'fixed_30': StopLossConfig.fixed(30),
            'fixed_40': StopLossConfig.fixed(40),
            'fixed_50': StopLossConfig.fixed(50),
            'fixed_70': StopLossConfig.fixed(70),
            
            'trailing_20': StopLossConfig.trailing(20),
            'trailing_30': StopLossConfig.trailing(30),
            'trailing_50': StopLossConfig.trailing(50),
            
            'time_5d': StopLossConfig.time(5),
            'time_10d': StopLossConfig.time(10),
            'time_20d': StopLossConfig.time(20),
            
            'atr_2x': StopLossConfig.atr(2.0),
            'atr_3x': StopLossConfig.atr(3.0),
            
            'pl_loss_5': StopLossConfig.pl_loss(5),
            'pl_loss_10': StopLossConfig.pl_loss(10),
            'pl_loss_15': StopLossConfig.pl_loss(15),
            
            'directional_3': StopLossConfig.directional(3),
            'directional_5': StopLossConfig.directional(5),
            'directional_7': StopLossConfig.directional(7),
            
            # NEW: COMBINED STOPS
            'combined_5_3': StopLossConfig.combined(5, 3),
            'combined_7_5': StopLossConfig.combined(7, 5),
            'combined_10_3': StopLossConfig.combined(10, 3),
        }
    
    @staticmethod
    def apply(base_config, stop_config):
        """Apply stop-loss configuration to base config"""
        merged = base_config.copy()
        
        merged['stop_loss_enabled'] = stop_config.get('enabled', False)
        
        if merged['stop_loss_enabled']:
            sl_config = {
                'type': stop_config['type'],
                'value': stop_config['value']
            }
            
            if 'trailing_distance' in stop_config:
                sl_config['trailing_distance'] = stop_config['trailing_distance']
            
            merged['stop_loss_config'] = sl_config
        
        return merged


# ============================================================
# BASELINE STOP-LOSS CONFIGURATION HELPER
# ============================================================
def configure_baseline_stop_loss(base_config, stop_loss_config, optimization_config, verbose=True):
    """
    Configure stop-loss for baseline test with pre-defined variables.
    
    Simplifies baseline configuration by:
    1. Pre-defining ALL stop-loss variables (avoids NameError)
    2. Using flat if/elif/else structure (avoids indentation errors)
    3. Printing stop-loss info (if verbose)
    4. Returning properly configured config
    
    Args:
        base_config: Base configuration dict (e.g., optimized_config)
        stop_loss_config: STOP_LOSS_CONFIG dict
        optimization_config: OPTIMIZATION_CONFIG dict with param_grid
        verbose: If True, print stop-loss configuration info
    
    Returns:
        tuple: (configured_config, sl_values)
            - configured_config: Config with proper stop_loss_config
            - sl_values: Dict with extracted SL values for reference
    
    Example:
        baseline_config, sl_values = configure_baseline_stop_loss(
            optimized_config, STOP_LOSS_CONFIG, OPTIMIZATION_CONFIG
        )
    """
    param_grid = optimization_config.get('param_grid', {})
    sl_enabled = stop_loss_config.get('enable_in', {}).get('baseline', False)
    
    # Pre-define ALL stop-loss variables (avoids NameError in any branch)
    sl_values = {
        'simple': param_grid.get('stop_loss_values', [0.04])[0],
        'pl_loss': param_grid.get('combined_pl_loss', [0.10])[0],
        'directional': param_grid.get('combined_directional', [0.04])[0],
        'logic': stop_loss_config.get('combined_settings', {}).get('logic', 'and'),
        'enabled': sl_enabled,
        'type': stop_loss_config.get('type', 'none')
    }
    
    # Print info (if verbose)
    if verbose:
        if not sl_enabled:
            print("Stop-Loss: DISABLED")
        elif stop_loss_config.get('type') == 'combined':
            logic_upper = sl_values['logic'].upper()
            print(f"Stop-Loss: Combined {logic_upper} (P&L {sl_values['pl_loss']*100:.0f}% {logic_upper} Directional {sl_values['directional']*100:.0f}%) - ENABLED")
        else:
            sl_type = stop_loss_config.get('type', 'directional')
            print(f"Stop-Loss: {sl_values['simple']*100:.0f}% {sl_type} - ENABLED")
    
    # Create configured config
    configured_config = base_config.copy()
    configured_config['stop_loss_enabled'] = sl_enabled
    
    # Configure stop_loss_config based on type (flat structure)
    if not sl_enabled:
        configured_config['stop_loss_config'] = {'enabled': False, 'type': 'none', 'value': 0}
    elif stop_loss_config.get('type') == 'combined':
        configured_config['stop_loss_config'] = stop_loss_config.copy()
        configured_config['stop_loss_config']['combined_settings'] = {
            'pl_loss': sl_values['pl_loss'],
            'directional': sl_values['directional'],
            'logic': sl_values['logic']
        }
    else:
        configured_config['stop_loss_config'] = stop_loss_config.copy()
        configured_config['stop_loss_config']['value'] = sl_values['simple']
    
    return configured_config, sl_values


def create_stoploss_comparison_chart(results, filename='stoploss_comparison.png', show_plots=True):
    """Create comparison chart"""
    try:
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('Stop-Loss Configuration Comparison', fontsize=16, fontweight='bold')
        
        names = [r['config']['name'] for r in results.values()]
        returns = [r['total_return'] for r in results.values()]
        sharpes = [r['sharpe'] for r in results.values()]
        drawdowns = [r['max_drawdown'] for r in results.values()]
        stop_counts = [r['stoploss_count'] for r in results.values()]
        
        ax1 = axes[0, 0]
        colors = ['#4CAF50' if r > 0 else '#f44336' for r in returns]
        ax1.barh(range(len(names)), returns, color=colors, alpha=0.7, edgecolor='black')
        ax1.set_yticks(range(len(names)))
        ax1.set_yticklabels(names, fontsize=9)
        ax1.set_xlabel('Total Return (%)')
        ax1.set_title('Total Return by Stop-Loss Type', fontsize=12, fontweight='bold')
        ax1.axvline(x=0, color='black', linestyle='-', linewidth=1)
        ax1.grid(True, alpha=0.3, axis='x')
        
        ax2 = axes[0, 1]
        colors_sharpe = ['#4CAF50' if s > 1 else '#FF9800' if s > 0 else '#f44336' for s in sharpes]
        ax2.barh(range(len(names)), sharpes, color=colors_sharpe, alpha=0.7, edgecolor='black')
        ax2.set_yticks(range(len(names)))
        ax2.set_yticklabels(names, fontsize=9)
        ax2.set_xlabel('Sharpe Ratio')
        ax2.set_title('Sharpe Ratio by Stop-Loss Type', fontsize=12, fontweight='bold')
        ax2.axvline(x=1, color='green', linestyle='--', linewidth=1, label='Good (>1)')
        ax2.axvline(x=0, color='black', linestyle='-', linewidth=1)
        ax2.legend()
        ax2.grid(True, alpha=0.3, axis='x')
        
        ax3 = axes[1, 0]
        ax3.barh(range(len(names)), drawdowns, color='#f44336', alpha=0.7, edgecolor='black')
        ax3.set_yticks(range(len(names)))
        ax3.set_yticklabels(names, fontsize=9)
        ax3.set_xlabel('Maximum Drawdown (%)')
        ax3.set_title('Maximum Drawdown (Lower is Better)', fontsize=12, fontweight='bold')
        ax3.grid(True, alpha=0.3, axis='x')
        
        ax4 = axes[1, 1]
        ax4.barh(range(len(names)), stop_counts, color='#2196F3', alpha=0.7, edgecolor='black')
        ax4.set_yticks(range(len(names)))
        ax4.set_yticklabels(names, fontsize=9)
        ax4.set_xlabel('Number of Stop-Loss Exits')
        ax4.set_title('Stop-Loss Frequency', fontsize=12, fontweight='bold')
        ax4.grid(True, alpha=0.3, axis='x')
        
        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        
        if show_plots:
            plt.show()
        else:
            plt.close()
        
        print(f"Comparison chart saved: {filename}")
        
    except Exception as e:
        print(f"Failed to create comparison chart: {e}")



# ============================================================
# DATA PRELOADING FUNCTION (FOR OPTIMIZATION)
# ============================================================
def preload_options_data(config, progress_widgets=None):
    """
    Preload options data for optimization.
    Loads data ONCE and returns cache.
    
    Returns:
        tuple: (lean_df, options_cache)
            - lean_df: DataFrame with IV lean history
            - options_cache: dict {date: DataFrame} with options data
    """
    if progress_widgets:
        progress_bar, status_label, monitor, start_time = progress_widgets
        status_label.value = "<b style='color:#0066cc'>🔄 Preloading options data (ONCE)...</b>"
        progress_bar.value = 5
    
    # Extract config
    from datetime import datetime, timedelta
    import pandas as pd
    import numpy as np
    import gc
    
    start_date = datetime.strptime(config['start_date'], '%Y-%m-%d').date()
    end_date = datetime.strptime(config['end_date'], '%Y-%m-%d').date()
    symbol = config['symbol']
    dte_target = config.get('dte_target', 30)
    lookback_period = config.get('lookback_period', 60)
    chunk_months = config.get('chunk_months', 1)  # Default 1 month (~30 days), not 3
    
    # Calculate date chunks
    data_start = start_date - timedelta(days=lookback_period + 60)
    
    date_chunks = []
    current_chunk_start = data_start
    while current_chunk_start <= end_date:
        # Use chunk_days_options if available, otherwise chunk_months * 30
        chunk_days = config.get('chunk_days_options', chunk_months * 30)
        chunk_end = min(
            current_chunk_start + timedelta(days=chunk_days),
            end_date
        )
        date_chunks.append((current_chunk_start, chunk_end))
        current_chunk_start = chunk_end + timedelta(days=1)
    
    # Store lean calculations
    lean_history = []
    all_options_data = []  # List to collect all options DataFrames
    
    # Track time for ETA
    preload_start_time = time.time()
    
    try:
        # Use api_call with caching instead of direct ivol API
        cache_config = config.get('cache_config')
        
        # Process each chunk
        for chunk_idx, (chunk_start, chunk_end) in enumerate(date_chunks):
            if progress_widgets:
                # Use update_progress for full display with ETA, CPU, RAM
                update_progress(
                    progress_bar, status_label, monitor,
                    current=chunk_idx + 1,
                    total=len(date_chunks),
                    start_time=preload_start_time,
                    message=f"🔄 Loading chunk {chunk_idx+1}/{len(date_chunks)}"
                )
            
            # Use api_call with caching (supports disk + memory cache)
            raw_data = api_call(
                '/equities/eod/options-rawiv',
                cache_config,
                symbol=symbol,
                from_=chunk_start.strftime('%Y-%m-%d'),
                to=chunk_end.strftime('%Y-%m-%d'),
                debug=cache_config.get('debug', False) if cache_config else False
            )
            
            if raw_data is None:
                continue
            
            # api_call returns dict with 'data' key
            if isinstance(raw_data, dict) and 'data' in raw_data:
                df = pd.DataFrame(raw_data['data'])
            else:
                df = pd.DataFrame(raw_data)
            
            if df.empty:
                continue
            
            # Essential columns
            essential_cols = ['date', 'expiration', 'strike', 'Call/Put', 'iv', 'Adjusted close']
            if 'bid' in df.columns:
                essential_cols.append('bid')
            if 'ask' in df.columns:
                essential_cols.append('ask')

            df = df[essential_cols].copy()
            
            # Process bid/ask
            if 'bid' in df.columns:
                df['bid'] = pd.to_numeric(df['bid'], errors='coerce').astype('float32')
            else:
                df['bid'] = np.nan

            if 'ask' in df.columns:
                df['ask'] = pd.to_numeric(df['ask'], errors='coerce').astype('float32')
            else:
                df['ask'] = np.nan

            # Calculate mid price
            df['mid'] = (df['bid'] + df['ask']) / 2
            df['mid'] = df['mid'].fillna(df['iv'])
            
            df['date'] = pd.to_datetime(df['date']).dt.date
            df['expiration'] = pd.to_datetime(df['expiration']).dt.date
            df['strike'] = pd.to_numeric(df['strike'], errors='coerce').astype('float32')
            df['iv'] = pd.to_numeric(df['iv'], errors='coerce').astype('float32')
            df['Adjusted close'] = pd.to_numeric(df['Adjusted close'], errors='coerce').astype('float32')
            
            df['dte'] = (pd.to_datetime(df['expiration']) - pd.to_datetime(df['date'])).dt.days
            df['dte'] = df['dte'].astype('int16')
            
            df = df.dropna(subset=['strike', 'iv', 'Adjusted close'])
            
            if df.empty:
                del df
                gc.collect()
                continue

            # Collect all options data
            all_options_data.append(df.copy())
            
            # Calculate lean for this chunk
            trading_dates = sorted(df['date'].unique())
            
            for current_date in trading_dates:
                day_data = df[df['date'] == current_date]
                
                if day_data.empty:
                    continue
                
                stock_price = float(day_data['Adjusted close'].iloc[0])
                
                dte_filtered = day_data[
                    (day_data['dte'] >= dte_target - 7) & 
                    (day_data['dte'] <= dte_target + 7)
                ]
                
                if dte_filtered.empty:
                    continue
                
                dte_filtered = dte_filtered.copy()
                dte_filtered['strike_diff'] = abs(dte_filtered['strike'] - stock_price)
                atm_idx = dte_filtered['strike_diff'].idxmin()
                atm_strike = float(dte_filtered.loc[atm_idx, 'strike'])
                
                atm_options = dte_filtered[dte_filtered['strike'] == atm_strike]
                atm_call = atm_options[atm_options['type'] == 'C']
                atm_put = atm_options[atm_options['type'] == 'P']
                
                if not atm_call.empty and not atm_put.empty:
                    call_iv = float(atm_call['iv'].iloc[0])
                    put_iv = float(atm_put['iv'].iloc[0])
                    
                    if pd.notna(call_iv) and pd.notna(put_iv) and call_iv > 0 and put_iv > 0:
                        iv_lean = call_iv - put_iv
                        
                        lean_history.append({
                            'date': current_date,
                            'stock_price': stock_price,
                            'iv_lean': iv_lean
                        })
            
            del df, raw_data
            gc.collect()
        
        lean_df = pd.DataFrame(lean_history)
        lean_df['stock_price'] = lean_df['stock_price'].astype('float32')
        lean_df['iv_lean'] = lean_df['iv_lean'].astype('float32')
        
        # Combine all options data into single DataFrame
        if all_options_data:
            options_df = pd.concat(all_options_data, ignore_index=True)
            # Ensure date column is properly formatted
            options_df['date'] = pd.to_datetime(options_df['date']).dt.date
            options_df['expiration'] = pd.to_datetime(options_df['expiration']).dt.date
        else:
            options_df = pd.DataFrame()
        
        del lean_history, all_options_data
        gc.collect()
        
        if progress_widgets:
            status_label.value = f"<b style='color:#00cc00'>✓ Data preloaded: {len(lean_df)} days, {len(options_df)} options records</b>"
            progress_bar.value = 35
        
        print(f"✓ Data preloaded: {len(lean_df)} days, {len(options_df)} options records")
        
        return lean_df, options_df
        
    except Exception as e:
        print(f"Error preloading data: {e}")
        return pd.DataFrame(), {}


# ============================================================
# UNIVERSAL DATA PRELOADER V2 (NEW!)
# ============================================================
def preload_data_universal(config, data_requests=None, debug=False):
    """
    NOTE: 'debug' parameter is deprecated - use config['debuginfo'] instead
    (kept for backward compatibility, but ignored)
    """
    """
    🚀 TRULY UNIVERSAL DATA PRELOADER - Works with ANY API endpoint!
    
    Supports:
    - EOD data: options-rawiv, stock-prices, ivs-by-delta, ivx, etc.
    - Intraday data: OPTIONS_INTRADAY, stock intraday, etc.
    - Any custom endpoint with any parameters
    - Automatic chunking for date ranges
    - Manual single-date requests
    
    Args:
        config: Strategy configuration (start_date, end_date, symbol)
        data_requests: List of data requests to load. If None, tries auto-detection.
                      
                      Format:
                      [
                          {
                              'name': 'options_data',          # Your name for this dataset
                              'endpoint': '/equities/eod/options-rawiv',
                              'params': {...},                 # Base params (symbol, etc.)
                              'chunking': {                    # Optional: for date-range data
                                  'enabled': True,
                                  'date_param': 'from_',       # Param name for start date
                                  'date_param_to': 'to',       # Param name for end date
                                  'chunk_days': 90             # Chunk size in days
                              },
                              'post_process': lambda df: df,   # Optional: process DataFrame
                          },
                          {
                              'name': 'ivx_data',
                              'endpoint': '/equities/eod/ivx',
                              'params': {
                                  'symbol': config['symbol'],
                                  'from_': config['start_date'],
                                  'to': config['end_date']
                              },
                              'chunking': {'enabled': False}   # Single request
                          },
                          {
                              'name': 'options_intraday',
                              'endpoint': '/equities/intraday/options-rawiv',
                              'params': {
                                  'symbol': config['symbol']
                              },
                              'date_list': True,               # Load for each date separately
                              'date_param': 'date'
                          }
                      ]
    
    Returns:
        dict: Preloaded data with keys like:
              {
                  '_preloaded_options_data': DataFrame,
                  '_preloaded_ivx_data': DataFrame,
                  '_preloaded_options_intraday': DataFrame,
                  '_stats': {...}
              }
    
    Usage in strategy:
        # Check for ANY preloaded data
        if any(k.startswith('_preloaded_') for k in config):
            options_df = config.get('_preloaded_options_data', pd.DataFrame()).copy()
            ivx_df = config.get('_preloaded_ivx_data', pd.DataFrame()).copy()
        else:
            # Load fresh
            ...
    """
    
    # ✅ AUTO-DETECT strategy_type if missing (needed for filtering & data requests)
    if 'strategy_type' not in config or not config['strategy_type']:
        config['strategy_type'] = _auto_detect_strategy_type(config)
    
    print("\n" + "="*80)
    print("🚀 UNIVERSAL PRELOADER V2 - Supports ANY endpoint (EOD/Intraday/IVX/etc.)")
    print("="*80)
    start_time = time.time()
    
    # Extract common config
    start_date = datetime.strptime(config['start_date'], '%Y-%m-%d').date()
    end_date = datetime.strptime(config['end_date'], '%Y-%m-%d').date()
    symbol = config['symbol']
    cache_config = config.get('cache_config', get_cache_config())
    debuginfo = config.get('debuginfo', 0)  # Extract debuginfo level (0=silent, 1=basic, 2=detailed, 3=verbose)
    
    # Auto-detection if not specified
    if data_requests is None:
        data_requests = _auto_detect_requests(config)
        print(f"\n🔍 Auto-detected {len(data_requests)} data requests from config")
    
    preloaded = {}
    total_rows = 0
    
    # Process each data request
    for req_idx, request in enumerate(data_requests, 1):
        req_name = request['name']
        endpoint = request['endpoint']
        base_params = request.get('params', {})
        chunking = request.get('chunking', {'enabled': False})
        post_process = request.get('post_process', None)
        date_list = request.get('date_list', False)
        
        # ✅ FIX: Use extended_start_date if provided (for IVX lookback data)
        request_start_date = request.get('extended_start_date', start_date)
        request_end_date = end_date
        
        print(f"\n[{req_idx}/{len(data_requests)}] 📊 Loading: {req_name}")
        print(f"           Endpoint: {endpoint}")
        if request_start_date != start_date:
            print(f"           📅 Extended range: {request_start_date} to {request_end_date} (includes lookback history)")
        
        all_data = []
        
        # ========================================================
        # MODE 1: DATE LIST (one request per date, e.g., intraday)
        # ========================================================
        if date_list:
            date_param = request.get('date_param', 'date')
            trading_days = pd.bdate_range(request_start_date, request_end_date).date
            
            print(f"           Mode: Date list ({len(trading_days)} dates)")
            
            for day_idx, date in enumerate(trading_days):
                params = base_params.copy()
                params[date_param] = date.strftime('%Y-%m-%d')
                
                if day_idx % max(1, len(trading_days) // 10) == 0:
                    print(f"           Progress: {day_idx}/{len(trading_days)} dates...")
                
                response = api_call(endpoint, cache_config, debug=debuginfo, **params)
                if response and 'data' in response:
                    df = pd.DataFrame(response['data'])
                    if len(df) > 0:
                        all_data.append(df)
        
        # ========================================================
        # MODE 2: CHUNKED LOADING (date ranges in chunks)
        # ========================================================
        elif chunking.get('enabled', False):
            date_param_from = chunking.get('date_param', 'from_')
            date_param_to = chunking.get('date_param_to', 'to')
            chunk_days = chunking.get('chunk_days', 30)
            chunk_size = timedelta(days=chunk_days)
            per_cp = chunking.get('per_cp', False)  # Separate requests for C and P
            
            # ✅ FIX: Use request_start_date (may be extended for lookback)
            current = request_start_date
            chunks = []
            while current <= request_end_date:
                chunk_end = min(current + chunk_size, request_end_date)
                chunks.append((current, chunk_end))
                current = chunk_end + timedelta(days=1)
            
            # If per_cp=True, we need separate requests for Calls and Puts
            cp_types = ['C', 'P'] if per_cp else [None]
            total_requests = len(chunks) * len(cp_types)
            
            if per_cp:
                print(f"           Mode: Chunked ({len(chunks)} chunks × 2 types = {total_requests} requests)")
            else:
                print(f"           Mode: Chunked ({len(chunks)} chunks of {chunk_days} days)")
            
            request_num = 0
            for cp_type in cp_types:
                for chunk_idx, (chunk_start, chunk_end) in enumerate(chunks):
                    params = base_params.copy()
                    params[date_param_from] = chunk_start.strftime('%Y-%m-%d')
                    params[date_param_to] = chunk_end.strftime('%Y-%m-%d')
                    
                    if cp_type:
                        params['cp'] = cp_type
                        
                        # ⚠️ CRITICAL FIX: Puts have NEGATIVE delta!
                        # If using delta filter, invert delta range for Puts
                        if cp_type == 'P' and 'deltaFrom' in params and 'deltaTo' in params:
                            # Swap and negate: deltaFrom=0.01, deltaTo=0.99 → deltaFrom=-0.99, deltaTo=-0.01
                            original_from = params['deltaFrom']
                            original_to = params['deltaTo']
                            params['deltaFrom'] = -original_to  # -0.99
                            params['deltaTo'] = -original_from  # -0.01
                    
                    request_num += 1
                    if request_num % max(1, total_requests // 5) == 0 or request_num == 1:
                        cp_label = f" ({cp_type})" if cp_type else ""
                        print(f"           Progress: {request_num}/{total_requests}{cp_label}...")
                    
                    if debuginfo >= 2:
                        cp_label = f" ({cp_type})" if cp_type else ""
                        print(f"           🔍 DEBUG: Requesting {chunk_start} to {chunk_end}{cp_label}... params={params}")
                    
                    response = api_call(endpoint, cache_config, debug=debuginfo, **params)
                    if response and 'data' in response:
                        df = pd.DataFrame(response['data'])
                        if len(df) > 0:
                            # Add cp type if not in response
                            if cp_type and 'type' not in df.columns and 'optionType' not in df.columns:
                                df['type'] = cp_type
                            all_data.append(df)
                            if debuginfo >= 2:
                                print(f"           ✓ Loaded {len(df)} rows for {cp_type if cp_type else 'both types'}")
                        elif debuginfo >= 2:
                            print(f"           ⚠️ Empty response for {cp_type if cp_type else 'both types'}")
                    elif debuginfo >= 2:
                        print(f"           ❌ No data in response for {cp_type if cp_type else 'both types'}")
        
        # ========================================================
        # MODE 3: SINGLE REQUEST (no chunking/date list)
        # ========================================================
        else:
            print(f"           Mode: Single request")
            
            params = base_params.copy()
            response = api_call(endpoint, cache_config, debug=debuginfo, **params)
            if response and 'data' in response:
                df = pd.DataFrame(response['data'])
                if len(df) > 0:
                    all_data.append(df)
        
        # ========================================================
        # COMBINE AND STORE
        # ========================================================
        if len(all_data) > 0:
            combined_df = pd.concat(all_data, ignore_index=True)
            
            # Apply post-processing if provided
            if post_process is not None:
                try:
                    combined_df = post_process(combined_df)
                except Exception as e:
                    print(f"           ⚠️  Post-processing failed: {e}")
            
            # Auto-process common date columns
            combined_df = _auto_process_dates(combined_df)
            
            # Normalize options columns (Call/Put → type with C/P)
            combined_df = _normalize_options_columns(combined_df)
            
            # Store with standardized key
            key = f"_preloaded_{req_name}"
            preloaded[key] = combined_df
            total_rows += len(combined_df)
            
            print(f"           ✓ Loaded: {len(combined_df):,} rows → {key}")
        else:
            print(f"           ⚠️  No data returned")
    
    # ========================================================
    # SUMMARY
    # ========================================================
    elapsed = time.time() - start_time
    
    # Collect detailed stats for each dataset
    dataset_details = {}
    for k in preloaded.keys():
        if k.startswith('_preloaded_'):
            dataset_name = k.replace('_preloaded_', '')
            df = preloaded[k]
            dataset_details[dataset_name] = {
                'rows': len(df),
                'endpoint': None
            }
    
    # Map dataset names to endpoints from data_requests
    if data_requests:
        for req in data_requests:
            req_name = req.get('name', 'unknown')
            if req_name in dataset_details:
                dataset_details[req_name]['endpoint'] = req.get('endpoint', 'unknown')
    
    preloaded['_stats'] = {
        'load_time_seconds': int(elapsed),
        'total_rows': total_rows,
        'data_count': len([k for k in preloaded.keys() if k.startswith('_preloaded_')]),
        'datasets': [k.replace('_preloaded_', '') for k in preloaded.keys() if k.startswith('_preloaded_')],
        'dataset_details': dataset_details
    }
    
    print(f"\n{'='*80}")
    print(f"✅ PRELOAD COMPLETE:")
    print(f"   • Time: {int(elapsed)}s")
    print(f"   • Total rows: {total_rows:,}")
    print(f"   • Datasets: {preloaded['_stats']['data_count']}")
    for ds in preloaded['_stats']['datasets']:
        print(f"     - {ds}")
    print(f"   • Cached in RAM for 4-5x speedup! 🚀")
    print(f"{'='*80}\n")
    
    return preloaded


def _auto_detect_requests(config):
    """
    Auto-detect what data to load based on config keys.
    
    Priority for options endpoint selection:
    1. config['options_endpoint'] if explicitly set to valid value
    2. STRATEGIES[strategy_type]['options_filter'] if exists
    3. Fallback to options-rawiv
    
    Valid options_endpoint values:
    - 'stock-opts-by-param' → server-side filtering (10-20x less data)
    - 'options-rawiv' → all options data (legacy)
    - 'auto' or anything else → auto-detect based on strategy_type
    """
    from datetime import datetime, timedelta
    import pandas as pd
    
    requests = []
    
    # ========================================================
    # CALCULATE LOOKBACK EXTENSION FOR IVX DATA
    # ========================================================
    # IVX indicators need historical data BEFORE backtest start for lookback calculations
    start_date = datetime.strptime(config['start_date'], '%Y-%m-%d').date()
    end_date = datetime.strptime(config['end_date'], '%Y-%m-%d').date()
    
    lookback_period = config.get('lookback_period')
    if lookback_period is None:
        # Calculate from lookback_ratio
        lookback_ratio = config.get('lookback_ratio', 0.25)
        total_days = (end_date - start_date).days
        lookback_period = int(total_days * lookback_ratio)
    
    # Extend start date for IVX data: lookback + margin for weekends/holidays
    # Using 1.5x multiplier to account for weekends/holidays (similar to preload_ivx_zscore_cache)
    ivx_extended_start = start_date - timedelta(days=int(lookback_period * 1.5 + 30))
    
    # ========================================================
    # OPTIONS ENDPOINT SELECTION
    # ========================================================
    options_endpoint = config.get('options_endpoint', 'auto')
    strategy_type = config.get('strategy_type')
    strategy_def = STRATEGIES.get(strategy_type, {}) if strategy_type else {}
    options_filter = strategy_def.get('options_filter')
    
    # Priority 1: Explicitly specified endpoint
    if options_endpoint in ('options-rawiv', 'options_rawiv'):
        # Force raw-iv (all data)
        print(f"   📦 Using options-rawiv (explicitly requested)")
        requests.append({
            'name': 'options',
            'endpoint': '/equities/eod/options-rawiv',
            'params': {
                'symbol': config['symbol']
            },
            'chunking': {
                'enabled': True,
                'date_param': 'from_',
                'date_param_to': 'to',
                'chunk_days': config.get('chunk_days_options', 30)
            },
            'post_process': lambda df: _process_options_df(df)
        })
    
    elif options_endpoint == 'stock-opts-by-param':
        # Force stock-opts-by-param (optimized)
        if options_filter:
            # Use strategy's options_filter
            options_request = _build_options_by_param_request(config, options_filter)
            requests.append(options_request)
            print(f"   📦 Using stock-opts-by-param (explicitly requested, filter from {strategy_type})")
        else:
            # Use default filter for stock-opts-by-param
            default_filter = {
                'selection_type': 'delta',
                'delta_from': 0.0,
                'delta_to': 1.0,
                'dte_tracking_min': 0,  # ✅ Track until expiration
            }
            options_request = _build_options_by_param_request(config, default_filter)
            requests.append(options_request)
            print(f"   📦 Using stock-opts-by-param (explicitly requested, default filter)")
    
    # Priority 2: Auto-detect based on strategy_type (only if 'auto')
    elif options_endpoint == 'auto' and options_filter:
        # Strategy has options_filter → use stock-opts-by-param
        options_request = _build_options_by_param_request(config, options_filter)
        requests.append(options_request)
        print(f"   📦 Using stock-opts-by-param for {strategy_type} (auto-detected)")
    
    # Priority 3: Fallback to raw-iv
    else:
        # No options_filter → fallback to raw-iv
        requests.append({
            'name': 'options',
            'endpoint': '/equities/eod/options-rawiv',
            'params': {
                'symbol': config['symbol']
            },
            'chunking': {
                'enabled': True,
                'date_param': 'from_',
                'date_param_to': 'to',
                'chunk_days': config.get('chunk_days_options', 30)
            },
            'post_process': lambda df: _process_options_df(df)
        })
        print(f"   📦 Using options-rawiv (fallback, no strategy_type or options_filter)")
    
    # Load IV surface if strategy uses term structure
    if any(k in config for k in ['short_tenor', 'long_tenor', 'delta_target']):
        requests.append({
            'name': 'ivs_surface',
            'endpoint': '/equities/eod/ivs-by-delta',
            'params': {
                'symbol': config['symbol'],
                'deltaFrom': config.get('delta_target', 0.5) - 0.05,
                'deltaTo': config.get('delta_target', 0.5) + 0.05,
                'periodFrom': config.get('short_tenor', 30) - 7,
                'periodTo': config.get('long_tenor', 90) + 7
            },
            'chunking': {
                'enabled': True,
                'date_param': 'from_',
                'date_param_to': 'to',
                'chunk_days': config.get('chunk_days_options', 30)
            }
        })
    
    # Load IVX data if strategy has indicators that need it
    if strategy_def:
        indicators = strategy_def.get('indicators', [])
        needs_ivx = any(
            INDICATOR_REGISTRY.get(ind['name'], {}).get('inputs', []) == ['ivx_df']
            for ind in indicators
        )
        if needs_ivx:
            # ✅ FIX: Extend start date to include lookback period for indicator calculation
            # This ensures IVX data is loaded with sufficient history for rolling calculations
            requests.append({
                'name': 'ivx',
                'endpoint': '/equities/eod/ivx',
                'params': {
                    'symbol': config['symbol']
                },
                'chunking': {
                    'enabled': True,
                    'date_param': 'from_',
                    'date_param_to': 'to',
                    'chunk_days': config.get('chunk_days_stock', 180)
                },
                # ✅ NEW: Override start_date to load historical data for lookback
                'extended_start_date': ivx_extended_start
            })
    
    # Load stock prices
    requests.append({
        'name': 'stock',
        'endpoint': '/equities/eod/stock-prices',
        'params': {
            'symbol': config['symbol']
        },
        'chunking': {
            'enabled': True,
            'date_param': 'from_',
            'date_param_to': 'to',
            'chunk_days': config.get('chunk_days_stock', 180)  # Stock data is lightweight
        }
    })
    
    # ========================================================
    # AUTO-DETECT EARNINGS CALENDAR
    # ========================================================
    # Load earnings calendar if earnings_config is specified
    # Works with ANY strategy type (STRADDLE, IRON_CONDOR, etc.)
    earnings_config = config.get('earnings_config', {})
    earnings_mode = earnings_config.get('mode')
    
    if earnings_mode in ['trade_around', 'avoid']:
        print(f"   📅 Earnings mode: {earnings_mode} - loading earnings calendar")
        requests.append({
            'name': 'earnings',
            'endpoint': '/equities/eod/history-earnings-calendar',
            'params': {
                'symbols': config['symbol'],
                'startDate': config['start_date'],
                'endDate': config['end_date']
            },
            'chunking': {'enabled': False}  # Single request (lightweight)
        })
    
    return requests


def _build_options_by_param_request(config, options_filter):
    """
    Build options request using stock-opts-by-param endpoint.
    
    This provides 10-20x less data by filtering on the server side:
    - moneyness: filter by % distance from ATM (for ATM-based strategies)
    - delta: filter by option delta (for delta-based strategies)
    - dte: filter by days to expiration
    
    Args:
        config: Strategy configuration
        options_filter: Filter settings from STRATEGIES[type]['options_filter']
        
    Returns:
        Request dict for preload_data_universal
    """
    symbol = config['symbol']
    
    # DTE range calculation
    dte_target = config.get('dte_target', 45)
    dte_tolerance = config.get('dte_tolerance', 15)
    
    # ⚠️ CRITICAL: dte_from must be LOW ENOUGH to track positions until expiration!
    # For entry: we want dte_target ± dte_tolerance
    # For tracking: we need down to 0 DTE (expiration day) to avoid intrinsic settlement disasters!
    dte_tracking_min = options_filter.get('dte_tracking_min', 0)  # ✅ CRITICAL: Track until expiration (0 DTE)
    dte_from = dte_tracking_min  # ✅ Always load from min DTE to track ALL open positions
    dte_to = dte_target + dte_tolerance  # ✅ Simplified: no dte_buffer needed!
    
    # Base params
    params = {
        'symbol': symbol,
        'dteFrom': dte_from,
        'dteTo': dte_to,
    }
    
    # Selection type determines filtering method
    selection_type = options_filter.get('selection_type', 'moneyness')
    
    if selection_type == 'delta':
        # Delta-based filtering (IRON_CONDOR, STRANGLE, etc.)
        params['deltaFrom'] = options_filter.get('delta_from', 0.05)
        params['deltaTo'] = options_filter.get('delta_to', 0.50)
        filter_desc = f"delta {params['deltaFrom']:.2f}-{params['deltaTo']:.2f}"
    else:
        # Moneyness-based filtering (STRADDLE, IV_LEAN, etc.)
        # Use wider range to catch deep OTM positions after large moves
        params['moneynessFrom'] = options_filter.get('moneyness_from', -100)
        params['moneynessTo'] = options_filter.get('moneyness_to', 100)
        filter_desc = f"moneyness {params['moneynessFrom']}% to {params['moneynessTo']}%"
    
    print(f"\n   🎯 Options filter: DTE {dte_from}-{dte_to}, {filter_desc}")
    
    # ⚠️ CRITICAL: For delta filter, per_cp MUST be True (API requires explicit cp parameter)
    # For moneyness filter, per_cp can be False (API returns both C and P if cp not specified)
    # BUT: For safety and consistency, ALWAYS use per_cp=True to ensure we get both calls and puts!
    use_per_cp = True  # ✅ Always separate C/P requests for reliability
    
    return {
        'name': 'options',
        'endpoint': '/equities/eod/stock-opts-by-param',
        'params': params,
        'chunking': {
            'enabled': True,
            'date_param': 'startDate',
            'date_param_to': 'endDate',
            'chunk_days': 30,  # Monthly chunks
            'per_cp': use_per_cp,    # ✅ Separate requests for C and P
        },
        'post_process': lambda df: _process_options_by_param_df(df)
    }


def _process_options_by_param_df(df):
    """
    Process options DataFrame from stock-opts-by-param endpoint.
    
    Maps columns to standard format and calculates DTE if needed.
    
    API returns columns like:
    - c_date, expiration_date, price_strike, Bid, Ask, call_put, etc.
    """
    if df is None or df.empty:
        return df
    
    # Column mapping (stock-opts-by-param → standard format)
    # API returns: c_date, expiration_date, price_strike, Bid, Ask, call_put, openinterest, iv, etc.
    column_map = {
        # Date columns
        'c_date': 'date',
        'tradeDate': 'date',           # Alternative name
        # Expiration
        'expiration_date': 'expiration',
        'expirationDate': 'expiration',  # Alternative name
        # Option type
        'call_put': 'type',
        'optionType': 'type',           # Alternative name
        # Strike
        'price_strike': 'strike',
        'strikePrice': 'strike',        # Alternative name
        # Prices
        'Bid': 'bid',
        'bidPrice': 'bid',              # Alternative name
        'Ask': 'ask',
        'askPrice': 'ask',              # Alternative name
        # Other
        'openinterest': 'open_interest',
        'openInterest': 'open_interest',  # Alternative name
        'impliedVolatility': 'iv',       # Alternative name (iv already exists)
    }
    
    # Rename columns that exist
    for old_col, new_col in column_map.items():
        if old_col in df.columns and new_col not in df.columns:
            df = df.rename(columns={old_col: new_col})
    
    # Convert dates
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date']).dt.date
    if 'expiration' in df.columns:
        df['expiration'] = pd.to_datetime(df['expiration']).dt.date
    
    # Calculate DTE if not present
    if 'dte' not in df.columns and 'date' in df.columns and 'expiration' in df.columns:
        df = df.copy()
        df['dte'] = (pd.to_datetime(df['expiration']) - 
                     pd.to_datetime(df['date'])).dt.days
    
    # Normalize option type (C/P)
    if 'type' in df.columns:
        df['type'] = df['type'].str.upper().str[0]  # 'Call' → 'C', 'Put' → 'P'
    
    # Sort by date for time-series operations
    if 'date' in df.columns:
        if not df['date'].is_monotonic_increasing:
            df = df.sort_values('date').reset_index(drop=True)
    
    return df


def _process_options_df(df):
    """Process options DataFrame: dates + DTE + OPTIMIZATIONS (5-10x faster!)"""
    # Basic date processing
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date']).dt.date
    if 'expiration' in df.columns:
        df['expiration'] = pd.to_datetime(df['expiration']).dt.date
    
    if 'date' in df.columns and 'expiration' in df.columns:
        df = df.copy()
        df['dte'] = (pd.to_datetime(df['expiration']) - 
                     pd.to_datetime(df['date'])).dt.days
    
    # ========================================================
    # CRITICAL: SORT BY DATE FIRST! (Required for time-series)
    # ========================================================
    if 'date' in df.columns:
        # Check if already sorted (skip if yes, fast!)
        if not df['date'].is_monotonic_increasing:
            df = df.sort_values('date')  # ✅ Sort only if needed
    
    # ========================================================
    # AUTOMATIC OPTIMIZATIONS (applied by library)
    # ========================================================
    
    # These optimizations are SAFE to apply automatically:
    # - Categorical types for low-cardinality columns
    # - Optimized numeric types (float32/int16 instead of float64/int64)
    #
    # NOTE: We do NOT set index on 'date' in library functions because:
    # - It breaks existing code that uses .loc with non-date indices
    # - Requires all strategies to handle Series vs scalar results
    
    # Convert type to categorical (60% less RAM, 2x faster filtering)
    if 'type' in df.columns:
        df['type'] = df['type'].astype('category')
    # Legacy support for 'Call/Put' column
    elif 'Call/Put' in df.columns:
        df['Call/Put'] = df['Call/Put'].astype('category')
    
    # Optimize data types (50% less RAM)
    # float32 for prices (4 bytes instead of 8, enough precision)
    float32_cols = ['strike', 'bid', 'ask', 'iv', 'price', 'mid', 'delta', 'gamma', 'vega', 'theta']
    for col in float32_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').astype('float32')
    
    # int16 for DTE (2 bytes instead of 8, max 32767 days)
    if 'dte' in df.columns:
        df['dte'] = df['dte'].astype('int16')
    
    return df


def get_option_by_strike_exp(options_df, strike, expiration, opt_type):
    """
    Get option data for specific strike, expiration, and type.
    
    This helper works consistently across ALL API endpoints because
    preload_data_universal() normalizes columns to unified format.
    
    Args:
        options_df: DataFrame with options data (must have 'type', 'strike', 'expiration' columns)
        strike: Strike price (float)
        expiration: Expiration date (date object)
        opt_type: 'C' for call, 'P' for put (case-insensitive, also accepts 'Call'/'Put')
    
    Returns:
        dict with option data or None if not found
    
    Example:
        ```python
        # Get ATM call option
        call = get_option_by_strike_exp(options_today, 450.0, exp_date, 'C')
        
        # ✅ SAFE: Both patterns work with dict return type
        if call:  # Works! Empty dict is falsy, None is falsy
            price = (call['bid'] + call['ask']) / 2
        
        if call is not None:  # Also works!
            price = (call['bid'] + call['ask']) / 2
        ```
    
    Note:
        - Returns dict (not pandas.Series) for SAFE truth value checks
        - You can use `if call:` or `if call and put:` safely
        - Framework ensures 'type' column always exists with 'C'/'P' values
        - Works with both options-rawiv and stock-opts-by-param endpoints
    """
    if options_df is None or options_df.empty:
        return None
    
    # Determine type column (normalized 'type' or legacy 'Call/Put')
    if 'type' in options_df.columns:
        type_col = 'type'
    elif 'Call/Put' in options_df.columns:
        type_col = 'Call/Put'
    else:
        return None  # No type column found
    
    # Normalize input (accept 'Call', 'call', 'C', etc.)
    opt_type_normalized = opt_type.upper()[0] if opt_type else None
    
    # Filter options
    filtered = options_df[
        (options_df['strike'] == strike) &
        (options_df['expiration'] == expiration) &
        (options_df[type_col] == opt_type_normalized)
    ]
    
    if len(filtered) > 0:
        return filtered.iloc[0].to_dict()  # ✅ Return dict, not Series!
    return None


def _normalize_options_columns(df):
    """
    Normalize options DataFrame columns to unified format.
    
    Ensures ALL options data (from any endpoint) uses consistent column names:
    - 'type' column with 'C'/'P' values (not 'Call/Put' or 'call'/'put')
    
    This allows get_option_by_strike_exp() and other helpers to work
    consistently regardless of which API endpoint was used.
    
    Args:
        df: Options DataFrame (from options-rawiv, stock-opts-by-param, etc.)
    
    Returns:
        DataFrame with normalized columns
    """
    if df is None or df.empty:
        return df
    
    # Step 1: Rename 'Call/Put' → 'type' (options-rawiv uses 'Call/Put')
    if 'Call/Put' in df.columns and 'type' not in df.columns:
        df = df.rename(columns={'Call/Put': 'type'})
    
    # Step 2: Normalize values to 'C'/'P' format
    if 'type' in df.columns:
        # Handle various formats: 'Call'→'C', 'call'→'C', 'PUT'→'P', etc.
        df['type'] = df['type'].apply(
            lambda x: 'C' if str(x).upper().startswith('C') else 'P'
        )
    
    return df


def _auto_process_dates(df):
    """Auto-process common date columns + SORT BY DATE"""
    date_columns = ['date', 'expiration', 'trade_date', 'time']
    
    for col in date_columns:
        if col in df.columns:
            try:
                if col == 'time':
                    # Keep time as string or datetime
                    pass
                else:
                    df[col] = pd.to_datetime(df[col]).dt.date
            except:
                pass  # Already in correct format or not a date
    
    # ========================================================
    # CRITICAL: SORT BY DATE! (Required for time-series)
    # ========================================================
    if 'date' in df.columns:
        # Check if already sorted (O(1) check vs O(N log N) sort)
        if not df['date'].is_monotonic_increasing:
            df = df.sort_values('date')  # ✅ Sort only if needed
    elif 'trade_date' in df.columns:
        if not df['trade_date'].is_monotonic_increasing:
            df = df.sort_values('trade_date')  # Alternative date column
    
    return df


# ============================================================================
# EARNINGS STRATEGY HELPERS
# ============================================================================

def parse_earnings_calendar(earnings_df):
    """
    Parse preloaded earnings DataFrame to list of dicts for strategy use.
    
    Framework loads earnings via _auto_detect_requests() when earnings_config['mode'] 
    is set. This helper converts the DataFrame to a sorted list for iteration.
    
    Args:
        earnings_df: Preloaded DataFrame from config.get('_preloaded_earnings')
    
    Returns:
        list: [{'date': datetime.date, 'estimate': float, 'reported': float, 
                'time_of_day': str}, ...]
        Sorted by date ascending.
    
    Usage in strategy:
        earnings_df = config.get('_preloaded_earnings', pd.DataFrame())
        earnings_events = parse_earnings_calendar(earnings_df)
        
        for event in earnings_events:
            earning_date = event['date']
            # ... process event
    """
    from datetime import datetime
    
    if earnings_df is None or earnings_df.empty:
        return []
    
    earnings_events = []
    for _, record in earnings_df.iterrows():
        earning_date = record.get('earning_date')
        if earning_date:
            # Handle both string and date formats
            if isinstance(earning_date, str):
                date_obj = datetime.strptime(earning_date, '%Y-%m-%d').date()
            elif hasattr(earning_date, 'date'):
                date_obj = earning_date.date()
            else:
                date_obj = earning_date
            
            earnings_events.append({
                'date': date_obj,
                'estimate': record.get('estimate'),
                'reported': record.get('reported_earning'),
                'time_of_day': record.get('time_of_day_code', 'UNK')
            })
    
    return sorted(earnings_events, key=lambda x: x['date'])


def find_next_trading_day(trading_days, target_date):
    """
    Find the next available trading day on or after target_date.
    
    Args:
        trading_days: Sorted list of trading days (datetime.date objects)
        target_date: Target date to find trading day for
    
    Returns:
        datetime.date: Next trading day, or None if not found
    
    Usage:
        trading_days = sorted(stock_df['date'].unique())
        entry_day = find_next_trading_day(trading_days, earning_date - timedelta(days=1))
        exit_day = find_next_trading_day(trading_days, earning_date + timedelta(days=1))
    """
    for day in trading_days:
        if day >= target_date:
            return day
    return None


# ============================================================================
# INDICATOR PRE-CALCULATION SYSTEM - Universal helpers
# ============================================================================

def auto_calculate_lookback_period(config, indicator_name, recommended_default=60):
    """
    Automatically calculate optimal lookback_period using configurable ratio.
    
    Universal Ratio Rule:
        lookback_period = backtest_period * lookback_ratio
    
    Where lookback_ratio can be:
        - From config: config.get('lookback_ratio', 1.0)  # User override
        - From indicator defaults (if ratio not in config)
        - Default: 1.0 (full period - use entire backtest history)
    
    This approach:
        - Scales automatically with backtest period
        - Allows optimization of lookback_ratio in param_grid
        - Intuitive: 0.5 = 50% of backtest period
    
    Args:
        config: Strategy configuration with start_date, end_date, lookback_ratio (optional)
        indicator_name: Name of indicator (for specific recommendations)
        recommended_default: Fallback if no ratio provided (legacy support)
    
    Returns:
        int: Optimal lookback_period (in trading days)
    
    Examples:
        - Backtest 250 days, ratio=1.00 (default) → lookback = 240 days (full period) ✅
        - Backtest 250 days, ratio=0.50 → lookback = 125 days (half period) ✅
        - Backtest 250 days, ratio=0.33 → lookback = 82 days (old 1/3 rule) ✅
    """
    from datetime import datetime
    
    # Calculate backtest period in calendar days
    start_date = datetime.strptime(config['start_date'], '%Y-%m-%d')
    end_date = datetime.strptime(config['end_date'], '%Y-%m-%d')
    calendar_days = (end_date - start_date).days
    
    # Convert to approximate trading days (252 / 365)
    trading_days = int(calendar_days * 0.69)  # ~69% are trading days
    
    # Get lookback_ratio from config or use default
    # Formula: lookback_period = backtest_period * lookback_ratio
    # Where: ratio = 1.0 means full period, 0.5 means half, 0.33 means 1/3
    lookback_ratio = config.get('lookback_ratio', 1.0)  # Default: 1.0 (full period)
    
    # Calculate lookback as percentage of backtest period
    optimal_lookback = int(trading_days * lookback_ratio)
    
    # Enforce minimum of 10 days (too small = noisy)
    optimal_lookback = max(optimal_lookback, 10)
    
    # Enforce maximum (don't exceed backtest period)
    optimal_lookback = min(optimal_lookback, trading_days - 10)
    
    return optimal_lookback


def get_required_indicators_for_strategy(strategy_type, config):
    """
    Automatically determines which indicators are needed for a strategy
    
    Args:
        strategy_type: Strategy name (e.g., 'IV_LEAN', 'IRON_CONDOR')
        config: Strategy configuration
    
    Returns:
        list: [{'name': 'iv_lean_zscore', 'params': {...}, 'required': True}, ...]
    """
    strategy = STRATEGIES.get(strategy_type)
    if not strategy or 'indicators' not in strategy:
        return []
    
    required_indicators = []
    
    for indicator_spec in strategy['indicators']:
        indicator_name = indicator_spec['name']
        
        if indicator_name not in INDICATOR_REGISTRY:
            print(f"⚠️  Warning: Unknown indicator '{indicator_name}' for {strategy_type}")
            continue
        
        # ✅ FIX: Start with optional_params as defaults (for indicators with no params_from_config)
        registry_entry = INDICATOR_REGISTRY.get(indicator_name, {})
        params = registry_entry.get('optional_params', {}).copy()  # ← Start with defaults!
        
        # Override with config values (config has priority!)
        for param_name in indicator_spec.get('params_from_config', []):
            if param_name in config:
                params[param_name] = config[param_name]
            elif param_name == 'lookback_period':
                # Auto-calculate from lookback_ratio (Parameter Translation Layer)
                params[param_name] = auto_calculate_lookback_period(config, indicator_name)
        
        required_indicators.append({
            'name': indicator_name,
            'params': params,
            'required': indicator_spec.get('required', False)
        })
    
    return required_indicators


def get_required_indicators_for_optimization(base_config, param_grid):
    """
    For optimization: collects ALL unique parameter combinations
    
    Args:
        base_config: Strategy config
        param_grid: Parameter grid for optimization
    
    Returns:
        list: [{'name': 'iv_lean_zscore', 'params': {...}}, ...] (all combinations)
    """
    import itertools
    
    strategy_type = base_config.get('strategy_type')
    strategy = STRATEGIES.get(strategy_type)
    
    if not strategy or 'indicators' not in strategy:
        return []
    
    all_indicators = []
    
    for indicator_spec in strategy['indicators']:
        indicator_name = indicator_spec['name']
        param_names = indicator_spec.get('params_from_config', [])
        
        # Get all combinations from param_grid
        param_lists = {}
        
        # Start with base values
        for param_name in param_names:
            if param_name in param_grid:
                # Use grid values
                param_lists[param_name] = param_grid[param_name]
            elif param_name in base_config:
                # Use base value
                param_lists[param_name] = [base_config[param_name]]
            elif param_name == 'lookback_period':
                # Auto-calculate using lookback_ratio (if available in param_grid or base_config)
                if 'lookback_ratio' in param_grid:
                    # Use all ratios from param_grid
                    param_lists[param_name] = [
                        auto_calculate_lookback_period(
                            {**base_config, 'lookback_ratio': ratio}, 
                            indicator_name
                        )
                        for ratio in param_grid['lookback_ratio']
                    ]
                elif 'lookback_ratio' in base_config:
                    # Use ratio from base_config
                    auto_lookback = auto_calculate_lookback_period(base_config, indicator_name)
                    param_lists[param_name] = [auto_lookback]
                else:
                    # Fallback: use default ratio 1.0
                    auto_lookback = auto_calculate_lookback_period(
                        {**base_config, 'lookback_ratio': 1.0}, 
                        indicator_name
                    )
                    param_lists[param_name] = [auto_lookback]
        
        # ✅ FIX: Handle indicators with NO parameters (e.g., iv_rank_ivx)
        if not param_lists:
            # No params from config - but still need to apply optional_params from registry!
            registry_entry = INDICATOR_REGISTRY.get(indicator_name, {})
            params = {}
            for key, value in registry_entry.get('optional_params', {}).items():
                params[key] = value
            
            all_indicators.append({
                'name': indicator_name,
                'params': params,  # ✅ FIXED: Use optional_params as defaults!
                'required': indicator_spec.get('required', False)
            })
            continue
        
        # Cartesian product of all param values
        keys = list(param_lists.keys())
        for values in itertools.product(*[param_lists[k] for k in keys]):
            combo = dict(zip(keys, values))
            
            # Add optional params from registry (only if not already set)
            registry_entry = INDICATOR_REGISTRY.get(indicator_name, {})
            for key, value in registry_entry.get('optional_params', {}).items():
                if key not in combo:
                    combo[key] = value
            
            all_indicators.append({
                'name': indicator_name,
                'params': combo,
                'required': indicator_spec.get('required', False)
            })
    
    return all_indicators


def precalculate_indicators_from_config(config, preloaded_data, param_grid=None):
    """
    🚀 UNIVERSAL INDICATOR PRE-CALCULATOR
    
    Automatically determines and calculates ALL indicators needed for:
    - Single backtest: indicators with base config params
    - Optimization: indicators with ALL param_grid combinations
    
    Args:
        config: Strategy config (must have 'strategy_type')
        preloaded_data: Dict with '_preloaded_options', '_preloaded_stock', etc.
        param_grid: Optional, for optimization mode
    
    Returns:
        dict: Indicator cache {cache_key: DataFrame}
              cache_key = (indicator_name, tuple(sorted(params.items())))
    """
    import time
    
    print("\n" + "="*80)
    print("🚀 UNIVERSAL INDICATOR PRE-CALCULATION")
    print("="*80)
    
    # Determine which indicators to calculate
    if param_grid:
        # OPTIMIZATION MODE: All param combinations
        indicators_to_calc = get_required_indicators_for_optimization(config, param_grid)
        mode = f"OPTIMIZATION ({len(indicators_to_calc)} combinations)"
    else:
        # SINGLE MODE: Base params only
        strategy_type = config.get('strategy_type')
        indicators_to_calc = get_required_indicators_for_strategy(strategy_type, config)
        mode = f"SINGLE BACKTEST ({len(indicators_to_calc)} indicators)"
    
    print(f"Mode: {mode}")
    
    if not indicators_to_calc:
        print("⚠️  No indicators needed for this strategy")
        print("="*80)
        return {}
    
    # Group by indicator name
    by_name = {}
    for ind_spec in indicators_to_calc:
        name = ind_spec['name']
        if name not in by_name:
            by_name[name] = []
        by_name[name].append(ind_spec)
    
    print(f"\nIndicators to calculate:")
    for name, specs in by_name.items():
        print(f"  • {name}: {len(specs)} combination(s)")
    print()
    
    indicator_cache = {}
    total_start = time.time()
    
    for indicator_name, indicator_specs in by_name.items():
        registry_entry = INDICATOR_REGISTRY.get(indicator_name)
        if not registry_entry:
            print(f"⚠️  Indicator '{indicator_name}' not found in INDICATOR_REGISTRY!")
            continue
        
        calculator_name = registry_entry['calculator']
        calculator_func = globals().get(calculator_name)
        
        if not calculator_func:
            print(f"⚠️  Calculator function '{calculator_name}' not found!")
            continue
        
        print(f"[{indicator_name}] Calculating {len(indicator_specs)} combination(s)...")
        
        for idx, spec in enumerate(indicator_specs, 1):
            params = spec['params']
            
            # Prepare inputs
            inputs = {}
            for input_name in registry_entry['inputs']:
                # Map: 'options_df' → '_preloaded_options'
                data_key = f'_preloaded_{input_name.replace("_df", "")}'
                data = preloaded_data.get(data_key, pd.DataFrame())
                
                # ✅ FIX: Add symbol column if missing (for proper multi-symbol support)
                if not data.empty and 'symbol' not in data.columns and 'symbol' in config:
                    data = data.copy()
                    data['symbol'] = config['symbol']
                
                inputs[input_name] = data
            
            # Check if data available
            if any(df.empty for df in inputs.values()):
                param_str = ", ".join(f"{k}={v}" for k, v in params.items()) if params else "(no params)"
                print(f"  [{idx}/{len(indicator_specs)}] {param_str}... ⚠️ SKIP - missing input data")
                continue
            
            # Show params for this calculation
            param_str = ", ".join(f"{k}={v}" for k, v in params.items()) if params else "(no params)"
            print(f"  [{idx}/{len(indicator_specs)}] {param_str}...", end=" ", flush=True)
            
            start_time = time.time()
            try:
                indicator_df = calculator_func(**inputs, **params)
                elapsed = time.time() - start_time
                
                if indicator_df.empty:
                    print(f" ⚠️ No data ({elapsed:.2f}s)")
                else:
                    print(f" ✓ {len(indicator_df)} days in {elapsed:.2f}s")
                    
                    # Create cache key
                    cache_key_params = tuple(params.get(p) for p in registry_entry['cache_key_params'])
                    cache_key = (indicator_name, cache_key_params)
                    
                    indicator_cache[cache_key] = indicator_df
                
            except Exception as e:
                print(f"❌ ERROR: {e}")
    
    total_elapsed = time.time() - total_start
    print(f"\n✅ Pre-calculated {len(indicator_cache)} indicator timeseries in {total_elapsed:.1f}s")
    print("="*80)
    
    return indicator_cache


def build_indicator_lookup(indicator_cache, config):
    """
    Creates unified dict for fast access to ALL indicators by (symbol, date)
    Supports multi-symbol data (if 'symbol' column present in indicator DataFrames)
    
    Args:
        indicator_cache: Dict from precalculate_indicators_from_config()
        config: Strategy config
    
    Returns:
        dict: {(symbol, date): {'iv_rank': 45.2, ...}} or {date: {...}} for single-symbol
    """
    strategy_type = config.get('strategy_type')
    strategy = STRATEGIES.get(strategy_type)
    
    if not strategy or 'indicators' not in strategy:
        return {}
    
    # Unified lookup
    by_key = {}
    
    if config.get('debuginfo', 0) >= 1:
        print(f"\n[build_indicator_lookup] Building lookup for {len(strategy['indicators'])} indicators...")
        print(f"   Cache contains {len(indicator_cache)} entries:")
        for cache_key in indicator_cache.keys():
            print(f"      {cache_key}")
    
    for indicator_spec in strategy['indicators']:
        indicator_name = indicator_spec['name']
        
        # Extract params from config to build cache key
        params = {}
        
        # ⚠️ FIRST: Get optional_params as DEFAULTS
        registry_entry = INDICATOR_REGISTRY.get(indicator_name, {})
        optional_params = registry_entry.get('optional_params', {})
        params.update(optional_params)  # Defaults first
        
        # ⚠️ THEN: Override with config values (config has priority!)
        for param_name in indicator_spec.get('params_from_config', []):
            if param_name in config:
                params[param_name] = config[param_name]  # ← Overrides defaults!
            elif param_name == 'lookback_period':
                # Auto-calculate from lookback_ratio
                params[param_name] = auto_calculate_lookback_period(config, indicator_name)
        
        # Build cache key
        cache_key_params = tuple(params.get(p) for p in registry_entry.get('cache_key_params', []))
        cache_key = (indicator_name, cache_key_params)
        
        # Debug
        if config.get('debuginfo', 0) >= 2:
            print(f"[build_indicator_lookup] Looking for {indicator_name} with key: {cache_key}")
            print(f"   Available keys in cache: {list(indicator_cache.keys())}")
        
        # Find in cache
        indicator_df = indicator_cache.get(cache_key)
        if indicator_df is None or indicator_df.empty:
            if config.get('debuginfo', 0) >= 1:
                print(f"⚠️  Indicator '{indicator_name}' not found in cache (key: {cache_key})")
            continue
        
        # Add all fields from this indicator
        for _, row in indicator_df.iterrows():
            date = row['date']
            
            # ✅ FIX: Normalize date to datetime.date (not Timestamp) for consistency with strategy
            if hasattr(date, 'date'):  # pandas.Timestamp or datetime.datetime
                date = date.date()  # Convert to datetime.date
            
            symbol = row.get('symbol', None)
            
            # Create key: (symbol, date) for multi-symbol, date for single-symbol
            key = (symbol, date) if symbol is not None else date
            
            if key not in by_key:
                by_key[key] = {}
            
            # Add all output fields (exclude 'date' and 'symbol')
            for field in registry_entry.get('outputs', []):
                if field not in ['date', 'symbol'] and field in row:
                    by_key[key][field] = row[field]
    
    return by_key


# ============================================================
# NEW: OPTIMIZATION FRAMEWORK
# ============================================================
def optimize_parameters(base_config, param_grid, strategy_function,
                       optimization_metric='sharpe', min_trades=0,
                       max_drawdown_limit=None, parallel=False,
                       export_each_combo=True, # ← NEW PARAMETER
                       optimization_config=None,  # ← NEW PARAMETER FOR PRESETS
                       results_folder=None  # ← NEW: Use existing folder or create new
                       ):  
    """
    Optimize strategy parameters across multiple combinations
    
    Args:
        base_config: Base configuration dict
        param_grid: Dict of parameters to optimize
            Example: {'z_score_entry': [1.0, 1.5, 2.0], 'z_score_exit': [0.1, 0.3, 0.5]}
        strategy_function: Strategy function to run
        optimization_metric: Metric to optimize ('sharpe', 'total_return', 'total_pnl', 'profit_factor', 'calmar')
        min_trades: Minimum number of trades required
        max_drawdown_limit: Maximum acceptable drawdown (e.g., 0.10 for 10%)
        parallel: Use parallel processing (not implemented yet)
        export_each_combo: If True, exports files for each combination  # ← 
    
    Returns:
        tuple: (results_df, best_params, results_folder)
    """
    
    # Check if optimization_config has preset and apply it automatically
    if optimization_config and isinstance(optimization_config, dict) and 'preset' in optimization_config:
        preset = optimization_config['preset']
        print(f"🔄 Auto-applying preset: {preset}")
        apply_optimization_preset(optimization_config, preset)
        print_preset_info(optimization_config)
        
        # Use preset parameters for grid and validation criteria
        param_grid = optimization_config['param_grid']
    
    # ✅ ALWAYS apply optimization_config values (with or without preset)
    if optimization_config and isinstance(optimization_config, dict):
        if 'min_trades' in optimization_config:
            min_trades = optimization_config['min_trades']
        if 'max_drawdown_limit' in optimization_config:
            max_drawdown_limit = optimization_config['max_drawdown_limit']
        if 'optimization_metric' in optimization_config:
            optimization_metric = optimization_config['optimization_metric']
        if 'parallel' in optimization_config:
            parallel = optimization_config['parallel']
        if 'export_each_combo' in optimization_config:
            export_each_combo = optimization_config['export_each_combo']
    
    # ═══ ADD AT THE BEGINNING OF FUNCTION ═══
    # Create results folder (or use provided one)
    if results_folder is None:
        results_folder = create_optimization_folder()
        print(f"📊 Results will be saved to: {results_folder}\n")
    else:
        print(f"📊 Using existing results folder: {results_folder}\n")
    
    # Record start time
    optimization_start_time = datetime.now()
    start_time_str = optimization_start_time.strftime('%Y-%m-%d %H:%M:%S')
    
    # Detect preloaded data
    preloaded_keys = [k for k in base_config.keys() if k.startswith('_preloaded_')]
    has_preloaded_data = len(preloaded_keys) > 0
    
    print("\n" + "="*80)
    print(" "*20 + "PARAMETER OPTIMIZATION")
    print("="*80)
    print(f"Strategy: {base_config.get('strategy_name', 'Unknown')}")
    print(f"Period: {base_config.get('start_date')} to {base_config.get('end_date')}")
    print(f"Optimization Metric: {optimization_metric}")
    print(f"Min Trades: {min_trades}")
    if max_drawdown_limit:
        print(f"Max Drawdown Limit: {max_drawdown_limit*100:.0f}%")
    if has_preloaded_data:
        print(f"✅ Preloaded data: {', '.join([k.replace('_preloaded_', '') for k in preloaded_keys])}")
    print(f"🕐 Started: {start_time_str}")
    print("="*80 + "\n")
    
    # Generate all combinations
    param_names = list(param_grid.keys())
    param_values = list(param_grid.values())
    all_combinations = list(product(*param_values))
    
    total_combinations = len(all_combinations)
    print(f"Testing {total_combinations} parameter combinations...")
    print(f"Parameters: {param_names}")
    print(f"Grid: {param_grid}\n")
    
    # Create SHARED progress context for all backtests
    try:
        from IPython.display import display
        import ipywidgets as widgets
        
        progress_bar = widgets.FloatProgress(
            value=0, min=0, max=100,
            description='Optimizing:',
            bar_style='info',
            layout=widgets.Layout(width='100%', height='30px')
        )
        
        status_label = widgets.HTML(value="<b>Starting optimization...</b>")
        display(widgets.VBox([progress_bar, status_label]))
        
        monitor = ResourceMonitor()
        opt_start_time = time.time()
        
        # Create shared progress context (will suppress individual backtest progress)
        shared_progress = {
            'progress_widgets': (progress_bar, status_label, monitor, opt_start_time),
            'is_optimization': True
        }
        has_widgets = True
    except:
        shared_progress = None
        has_widgets = False
        print("Running optimization (no progress bar)...")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # DEPRECATED: optimize_parameters should NOT preload data internally!
    # Data should be preloaded BEFORE calling optimize_parameters using preload_data_universal()
    # ═══════════════════════════════════════════════════════════════════════════
    # Check if data is already preloaded
    preloaded_keys = [k for k in base_config.keys() if k.startswith('_preloaded_')]
    
    # Initialize these variables for backward compatibility
    preloaded_lean_df = None
    preloaded_options_df = None
    use_legacy_preload = False
    
    if not preloaded_keys:
        # Fallback: use old preload_options_data (for backward compatibility)
        print("\n" + "="*80)
        print("📥 PRELOADING OPTIONS DATA (loads ONCE, reused for all combinations)")
        print("="*80)
        print("⚠️  WARNING: Data not preloaded! Using deprecated preload_options_data()")
        print("⚠️  Recommendation: Use preload_data_universal() before calling optimize_parameters()")
        print("="*80)
        
        preloaded_lean_df, preloaded_options_df = preload_options_data(
            base_config, 
            progress_widgets=shared_progress['progress_widgets'] if shared_progress else None
        )
        
        if preloaded_lean_df.empty:
            print("\n❌ ERROR: Failed to preload data. Cannot proceed with optimization.")
            return pd.DataFrame(), None
        
        use_legacy_preload = True
        print(f"✓ Preloading complete! Data will be reused for all {total_combinations} combinations")
        print("="*80 + "\n")
    else:
        print("\n✓ Using preloaded data from preload_data_universal() (recommended method)\n")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # RESET PROGRESS BAR FOR OPTIMIZATION LOOP
    # ═══════════════════════════════════════════════════════════════════════════
    if has_widgets:
        progress_bar.value = 0
        progress_bar.bar_style = 'info'
        status_label.value = "<b style='color:#0066cc'>Starting optimization loop...</b>"
    
    # Run backtests
    results = []
    start_time = time.time()
    
    for idx, param_combo in enumerate(all_combinations, 1):
        # Create test config
        test_config = base_config.copy()
        
        # Update parameters
        for param_name, param_value in zip(param_names, param_combo):
            test_config[param_name] = param_value
        
        # ═══════════════════════════════════════════════════════════════════
        # INDICATOR LOOKUP SUPPORT (v2.22+)
        # ═══════════════════════════════════════════════════════════════════
        # If base_config contains 'indicator_cache', build lookup for THIS combination
        # This ensures each run uses correct indicators for its parameters
        if 'indicator_cache' in base_config and 'indicator_cache' not in param_names:
            indicator_cache = base_config['indicator_cache']
            # Build lookup with CURRENT test_config (has correct dte_target, etc.)
            test_config['indicator_lookup'] = build_indicator_lookup(indicator_cache, test_config)
            # Remove cache from test_config (not needed in strategy)
            test_config.pop('indicator_cache', None)
        
        # ═══════════════════════════════════════════════════════════════════
        # COMBINED STOP-LOSS SUPPORT (v2.21+)
        # ═══════════════════════════════════════════════════════════════════
        # If param_grid contains 'combined_*' parameters, automatically
        # construct stop_loss_config['combined_settings'] from them
        combined_params = {}
        if 'combined_pl_loss' in test_config:
            combined_params['pl_loss'] = test_config.pop('combined_pl_loss')
        if 'combined_directional' in test_config:
            combined_params['directional'] = test_config.pop('combined_directional')
        if 'combined_logic' in test_config:
            combined_params['logic'] = test_config.pop('combined_logic')
        
        # If any combined_* params exist, update stop_loss_config
        if combined_params:
            if 'stop_loss_config' not in test_config:
                test_config['stop_loss_config'] = {}
            if 'combined_settings' not in test_config['stop_loss_config']:
                test_config['stop_loss_config']['combined_settings'] = {}
            
            # Merge combined_params into combined_settings
            test_config['stop_loss_config']['combined_settings'].update(combined_params)
            
            # Ensure type is set to 'combined'
            if test_config['stop_loss_config'].get('type') != 'combined':
                test_config['stop_loss_config']['type'] = 'combined'
            
            # ✨ CRITICAL: Enable stop-loss when combined_* params are used
            test_config['stop_loss_enabled'] = True
        
        # ═══════════════════════════════════════════════════════════════════
        # EARNINGS CONFIG SUPPORT (v2.22+)
        # ═══════════════════════════════════════════════════════════════════
        # If param_grid contains earnings-related parameters, automatically
        # update earnings_config with them
        # ✅ Use .get() NOT .pop() - keep params in test_config for format_params_string!
        earnings_params = {}
        if 'entry_days_before' in test_config:
            earnings_params['entry_days_before'] = test_config['entry_days_before']
        if 'exit_days_after' in test_config:
            earnings_params['exit_days_after'] = test_config['exit_days_after']
        if 'min_implied_move' in test_config:
            earnings_params['min_implied_move'] = test_config['min_implied_move']
        if 'iv_percentile_min' in test_config:
            earnings_params['iv_percentile_min'] = test_config['iv_percentile_min']
        if 'earnings_buffer_days' in test_config:
            earnings_params['buffer_days'] = test_config['earnings_buffer_days']
        
        # If any earnings params exist, update earnings_config
        if earnings_params:
            if 'earnings_config' not in test_config:
                test_config['earnings_config'] = {}
            
            # Merge earnings_params into earnings_config
            test_config['earnings_config'].update(earnings_params)
        
        # ═══════════════════════════════════════════════════════════════════
        # STOP-LOSS CONFIG SUPPORT
        # ═══════════════════════════════════════════════════════════════════
        # If param_grid contains stop_loss_pct, update stop_loss_config['value']
        if 'stop_loss_pct' in test_config:
            if 'stop_loss_config' not in test_config:
                test_config['stop_loss_config'] = {}
            test_config['stop_loss_config']['value'] = test_config['stop_loss_pct']
            test_config['stop_loss_enabled'] = True
        
        # Update name
        param_str = "_".join([f"{k}={v}" for k, v in zip(param_names, param_combo)])
        test_config['strategy_name'] = f"{base_config.get('strategy_name', 'Strategy')} [{param_str}]"
        
        # ═══ ADD PRELOADED DATA TO CONFIG ═══
        # Only add legacy preloaded data if it was loaded by preload_options_data
        if use_legacy_preload:
            test_config['_preloaded_lean_df'] = preloaded_lean_df
            test_config['_preloaded_options_cache'] = preloaded_options_df
        # Otherwise, data is already in base_config from preload_data_universal
        
        # ═══ CREATE COMPACT PARAMETER STRING EARLY (for progress display) ═══
        try:
            # ✅ Use format_params_string() for data-driven naming
            compact_params = format_params_string(test_config)
            
            # Add SL prefix if provided (from notebook loop)
            sl_prefix = test_config.get('_sl_prefix', '')
            if sl_prefix:
                # Format: SL3_cb1_Z1_E0.1_L60_DT45
                combo_name = f"{sl_prefix}_cb{idx}_{compact_params}"
                display_name = f"{sl_prefix}_{compact_params}"
            else:
                # ✅ FIXED: format_params_string() already includes SL in compact_params
                # No need to add it again (was causing duplicate SL100_SL100)
                combo_name = f"cb{idx}_{compact_params}"
                display_name = compact_params
            
            # -----------------------------
            # Print combo header BEFORE running backtest (so user sees params)
            # -----------------------------
            print("\n" + "="*80)
            print(f"[{idx}/{total_combinations}] {combo_name}")
            print("="*80)
            print(f"• Parameters : {param_str}")
            if test_config.get('stop_loss_enabled') and 'stop_loss_config' in test_config:
                sl_cfg = test_config['stop_loss_config']
                sl_type = sl_cfg.get('type', 'unknown')
                
                # Display Combined Stop-Loss with details
                if sl_type == 'combined':
                    combined_settings = sl_cfg.get('combined_settings', {})
                    pl_loss = combined_settings.get('pl_loss', 0)
                    directional = combined_settings.get('directional', 0)
                    logic = combined_settings.get('logic', 'and').upper()
                    sl_value_display = f"PL {pl_loss*100:.0f}% {logic} DIR {directional*100:.0f}%"
                    print(f"• Stop-loss  : {sl_type} -> {sl_value_display}")
                else:
                    # Display simple stop-loss types
                    sl_value = sl_cfg.get('value')
                    if isinstance(sl_value, (int, float)):
                        sl_value_display = f"{sl_value*100:.2f}%" if sl_type in ('pl_loss', 'fixed_pct', 'trailing', 'directional') else sl_value
                    else:
                        sl_value_display = sl_value
                    print(f"• Stop-loss  : {sl_type} -> {sl_value_display}")
            else:
                print("• Stop-loss  : disabled")


            # 🆕 NEW: Check for directional_settings (intraday inside stop-loss config)
            sl_cfg = test_config.get('stop_loss_config', {})
            if sl_cfg.get('type') == 'directional' and sl_cfg.get('enabled', False):
                dir_settings = sl_cfg.get('directional_settings', {})
                if dir_settings:
                    intraday_mode = dir_settings.get('intraday_mode', 'eod_only')
                    minute_interval = dir_settings.get('minute_interval', 'MINUTE_1')
                    min_days = dir_settings.get('min_days_before_check', 0)
                    
                    if intraday_mode == 'eod_only':
                        print(f"• Intraday SL: eod_only (no API calls)")
                    else:
                        print(f"• Intraday SL: {intraday_mode} ({minute_interval}, min_days={min_days})")
                else:
                    print("• Intraday SL: not configured (using EOD)")
            else:
                # Fallback: check old intraday_stops config for backward compatibility
                intraday_cfg = test_config.get('intraday_stops', {})
                if intraday_cfg.get('enabled', False):
                    intraday_pct = intraday_cfg.get('stop_pct')
                    pct_text = f"{intraday_pct*100:.2f}%" if isinstance(intraday_pct, (int, float)) else intraday_pct
                    print(f"• Intraday SL: enabled (OLD CONFIG - {pct_text}, min_days={intraday_cfg.get('min_days_before_intraday', 'n/a')})")
                else:
                    print("• Intraday SL: disabled")
            print("-"*80)

            # Update progress with compact name (after printing parameters)
            if has_widgets:
                # Use update_progress for full display with ETA, CPU, RAM
                update_progress(
                    progress_bar, status_label, monitor,
                    current=idx,
                    total=total_combinations,
                    start_time=start_time,
                    message=f"Testing: {display_name}"
                )
            else:
                if idx % max(1, total_combinations // 10) == 0:
                    print(f"[{idx}/{total_combinations}] {display_name}")
            
            # Create combo folder: SL3_c01_Z1.0_E0.1_PT20
            combo_folder = os.path.join(results_folder, combo_name)
            os.makedirs(combo_folder, exist_ok=True)
            
            # File prefix: SL3_c01_Z1.0_E0.1_PT20
            combo_prefix = combo_name
            
            # Run backtest WITH EXPORT AND CHARTS (saved but not displayed)
            analyzer = run_backtest(
                strategy_function,
                test_config,
                print_report=False,
                create_charts=export_each_combo,  # ← CREATE CHARTS (saved but not displayed)
                export_results=export_each_combo,  # ← MODIFIED
                progress_context=shared_progress,
                chart_filename=os.path.join(combo_folder, f'{combo_prefix}_chart.png') if export_each_combo else None,  # ← UNIVERSAL NAMING
                export_prefix=os.path.join(combo_folder, combo_prefix) if export_each_combo else None  # ← ADDED
            )
            
            # Check validity
            is_valid = True
            invalid_reason = ""
            
            if analyzer.metrics['total_trades'] < min_trades:
                is_valid = False
                invalid_reason = f"Too few trades ({analyzer.metrics['total_trades']})"
            
            if max_drawdown_limit and analyzer.metrics['max_drawdown'] > (max_drawdown_limit * 100):
                is_valid = False
                invalid_reason = f"Excessive drawdown ({analyzer.metrics['max_drawdown']:.1f}%)"
            
            # Print compact statistics for this combination
            status_symbol = "✓" if is_valid else "✗"
            status_color = "#00cc00" if is_valid else "#ff6666"
            
            # Print combination header (with SL)
            print(f"[{idx}/{total_combinations}] {combo_name}")
            print("-" * 100)
            
            # Print chart file if created
            if hasattr(analyzer, 'chart_file') and analyzer.chart_file:
                print(f"Chart saved: {analyzer.chart_file}")
            
            # Print exported files
            if hasattr(analyzer, 'exported_files') and analyzer.exported_files:
                for file_path, extra_info in analyzer.exported_files:
                    if extra_info:
                        print(f"Exported: {file_path} {extra_info}")
                    else:
                        print(f"Exported: {file_path}")
            
            # Print metrics with separator
            print("+" * 100)
            if is_valid:
                print(f"  {status_symbol} Return: {analyzer.metrics['total_return']:>7.2f}% | "
                      f"Sharpe: {analyzer.metrics['sharpe']:>6.2f} | "
                      f"Max DD: {analyzer.metrics['max_drawdown']:>6.2f}% | "
                      f"Trades: {analyzer.metrics['total_trades']:>3} | "
                      f"Win Rate: {analyzer.metrics['win_rate']:>5.1f}% | "
                      f"PF: {analyzer.metrics['profit_factor']:>5.2f}")
            else:
                print(f"  {status_symbol} INVALID: {invalid_reason}")
            print("+" * 100 + "\n")
            
            # Update widget status with last result
            if has_widgets:
                result_text = f"Return: {analyzer.metrics['total_return']:.1f}% | Sharpe: {analyzer.metrics['sharpe']:.2f}" if is_valid else invalid_reason
                
                # Get resource usage
                cpu_pct = monitor.get_cpu_percent()
                mem_info = monitor.get_memory_info()
                ram_mb = mem_info[0]  # process_mb
                resource_text = f"CPU: {cpu_pct:.0f}% | RAM: {ram_mb:.0f}MB"
                
                status_label.value = (
                    f"<b style='color:{status_color}'>[{idx}/{total_combinations}] {combo_name}</b><br>"
                    f"<span style='color:#666'>{result_text}</span><br>"
                    f"<span style='color:#999;font-size:10px'>{resource_text}</span>"
                )
            
            # Store results
            result = {
                'combination_id': idx,
                'is_valid': is_valid,
                'invalid_reason': invalid_reason,
                **{name: value for name, value in zip(param_names, param_combo)},
                'total_return': analyzer.metrics['total_return'],
                'sharpe': analyzer.metrics['sharpe'],
                'sortino': analyzer.metrics['sortino'],
                'calmar': analyzer.metrics['calmar'],
                'max_drawdown': analyzer.metrics['max_drawdown'],
                'win_rate': analyzer.metrics['win_rate'],
                'profit_factor': analyzer.metrics['profit_factor'],
                'total_trades': analyzer.metrics['total_trades'],
                'avg_win': analyzer.metrics['avg_win'],
                'avg_loss': analyzer.metrics['avg_loss'],
                'volatility': analyzer.metrics['volatility'],
            }
            
            results.append(result)
            
            # ═══ MEMORY CLEANUP AFTER EACH TEST ═══
            # Delete large objects to free RAM for next iteration
            
            # Clear references to preloaded data (prevents memory leaks)
            if use_legacy_preload:
                # Legacy preload method
                if '_preloaded_lean_df' in test_config:
                    del test_config['_preloaded_lean_df']
                if '_preloaded_options_cache' in test_config:
                    del test_config['_preloaded_options_cache']
            else:
                # Universal preloader - clear all preloaded keys
                for key in list(test_config.keys()):
                    if key.startswith('_preloaded_'):
                        del test_config[key]
            
            del analyzer, test_config
            gc.collect()
            
            # Show intermediate summary every 10 combinations (or at end)
            if idx % 10 == 0 or idx == total_combinations:
                valid_so_far = [r for r in results if r['is_valid']]
                if valid_so_far:
                    print("\n" + "="*80)
                    print(f"INTERMEDIATE SUMMARY ({idx}/{total_combinations} tested)")
                    print("="*80)
                    
                    # Sort by optimization metric
                    if optimization_metric == 'sharpe':
                        valid_so_far.sort(key=lambda x: x['sharpe'], reverse=True)
                    elif optimization_metric == 'total_return':
                        valid_so_far.sort(key=lambda x: x['total_return'], reverse=True)
                    elif optimization_metric == 'total_pnl':
                        valid_so_far.sort(key=lambda x: x['total_pnl'], reverse=True)
                    elif optimization_metric == 'profit_factor':
                        valid_so_far.sort(key=lambda x: x['profit_factor'], reverse=True)
                    elif optimization_metric == 'calmar':
                        valid_so_far.sort(key=lambda x: x['calmar'], reverse=True)
                    
                    # Show top 3
                    print(f"\n🏆 TOP 3 BY {optimization_metric.upper()}:")
                    print("-"*80)
                    for rank, res in enumerate(valid_so_far[:3], 1):
                        params_display = ", ".join([f"{name}={res[name]}" for name in param_names])
                        print(f"  {rank}. [{params_display}]")
                        print(f"     Return: {res['total_return']:>7.2f}% | "
                              f"Sharpe: {res['sharpe']:>6.2f} | "
                              f"Max DD: {res['max_drawdown']:>6.2f}% | "
                              f"Trades: {res['total_trades']:>3}")
                    
                    print(f"\nValid: {len(valid_so_far)}/{idx} | "
                          f"Invalid: {idx - len(valid_so_far)}/{idx}")
                    print("="*80 + "\n")
        
        except Exception as e:
            print(f"\n[{idx}/{total_combinations}] {param_str}")
            print("-" * 80)
            print(f"  ✗ ERROR: {str(e)}")
            import traceback
            print("  Full traceback:")
            traceback.print_exc()
            
            result = {
                'combination_id': idx,
                'is_valid': False,
                'invalid_reason': f"Error: {str(e)[:50]}",
                **{name: value for name, value in zip(param_names, param_combo)},
                'total_return': 0, 'sharpe': 0, 'sortino': 0, 'calmar': 0,
                'max_drawdown': 0, 'win_rate': 0, 'profit_factor': 0,
                'total_trades': 0, 'avg_win': 0, 'avg_loss': 0, 'volatility': 0
            }
            results.append(result)
    
    elapsed = time.time() - start_time
    
    if has_widgets:
        progress_bar.value = 100
        progress_bar.bar_style = 'success'
        status_label.value = f"<b style='color:#00cc00'>✓ Optimization complete in {int(elapsed)}s</b>"
    
    # Create results DataFrame
    results_df = pd.DataFrame(results)
    
    # Round numeric columns to 2 decimals
    numeric_columns = results_df.select_dtypes(include=['float64', 'float32', 'float']).columns
    for col in numeric_columns:
        results_df[col] = results_df[col].round(5)

    # ═══ ADD SUMMARY SAVE TO FOLDER ═══
    summary_path = os.path.join(results_folder, 'optimization_summary.csv')
    results_df.to_csv(summary_path, index=False)
    print(f"\n✓ Summary saved: {summary_path}")
    
    # Find best parameters
    valid_results = results_df[results_df['is_valid'] == True].copy()
    
    if len(valid_results) == 0:
        print("\n" + "="*80)
        print("WARNING: No valid combinations found!")
        print("Try relaxing constraints or checking parameter ranges")
        print("="*80)
        return results_df, None, results_folder
    
    # Select best based on metric
    if optimization_metric == 'sharpe':
        best_idx = valid_results['sharpe'].idxmax()
    elif optimization_metric == 'total_return':
        best_idx = valid_results['total_return'].idxmax()
    elif optimization_metric == 'total_pnl':
        best_idx = valid_results['total_pnl'].idxmax()
    elif optimization_metric == 'profit_factor':
        best_idx = valid_results['profit_factor'].idxmax()
    elif optimization_metric == 'calmar':
        best_idx = valid_results['calmar'].idxmax()
    else:
        best_idx = valid_results['sharpe'].idxmax()
    
    best_result = valid_results.loc[best_idx]
    
    # Extract best parameters
    best_params = {name: best_result[name] for name in param_names}
    
    # Add stop_loss_pct if it exists in config (it's handled separately in notebook)
    if 'stop_loss_config' in base_config and base_config['stop_loss_config']:
        stop_loss_value = base_config['stop_loss_config'].get('value')
        if stop_loss_value is not None:
            best_params['stop_loss_pct'] = stop_loss_value
    
    # Calculate total time
    optimization_end_time = datetime.now()
    total_duration = optimization_end_time - optimization_start_time
    end_time_str = optimization_end_time.strftime('%Y-%m-%d %H:%M:%S')
    duration_str = format_time(total_duration.total_seconds())
    
    # Print summary
    print("\n" + "="*120)
    print(" "*31 + "🏆 OPTIMIZATION COMPLETE 🏆")
    print(" "*31 + "=========================")
    print(f"  • Started              : {start_time_str}")
    print(f"  • Finished             : {end_time_str}")
    print(f"  • Total Duration       : {duration_str} ({int(total_duration.total_seconds())} seconds)")
    print(f"  • Average per run      : {total_duration.total_seconds() / total_combinations:.1f} seconds")
    print(f"  • Total combinations   : {total_combinations}")
    print(f"  • Valid combinations   : {len(valid_results)}")
    print(f"  • Invalid combinations : {len(results_df) - len(valid_results)}")
    
    print(f"\n📈 OPTIMIZATION METRIC:")
    print(f"  • Metric optimized     : {optimization_metric.upper()}")
    
    # Format best parameters in one line (with special formatting for stop_loss and combined)
    param_parts = []
    combined_params = {}
    
    for name, value in best_params.items():
        # Collect combined_* parameters separately
        if name == 'combined_pl_loss':
            combined_params['pl_loss'] = value
        elif name == 'combined_directional':
            combined_params['directional'] = value
        elif name == 'combined_logic':
            combined_params['logic'] = value
        elif name == 'stop_loss_pct':
            param_parts.append(f"stop_loss={value*100:.0f}%")
        else:
            param_parts.append(f"{name}={value}")
    
    # Add combined stop as one formatted parameter
    if combined_params:
        pl = combined_params.get('pl_loss', 0) * 100
        dr = combined_params.get('directional', 0) * 100
        logic = combined_params.get('logic', 'or').upper()
        param_parts.append(f"combined_stop=PL{pl:.0f}% {logic} DIR{dr:.0f}%")
    
    param_str = ", ".join(param_parts)
    print(f"  • Best parameters      : {param_str}")
    
    # Add intraday stop-loss info if enabled
    intraday_stops = base_config.get('intraday_stops', {})
    if intraday_stops.get('enabled', False):
        intraday_pct = intraday_stops.get('stop_pct', 0.03) * 100
        intraday_days = intraday_stops.get('min_days_before_intraday', 3)
        print(f"  • Intraday stop-loss   : Enabled ({intraday_pct:.0f}% after {intraday_days} days)")
    
    print(f"\n🏆 BEST PERFORMANCE:")
    print(f"  • Total Return         : {best_result['total_return']:>10.2f}%")
    print(f"  • Sharpe Ratio         : {best_result['sharpe']:>10.2f}")
    print(f"  • Max Drawdown         : {best_result['max_drawdown']:>10.2f}%")
    print(f"  • Win Rate             : {best_result['win_rate']:>10.1f}%")
    print(f"  • Profit Factor        : {best_result['profit_factor']:>10.2f}")
    print(f"  • Total Trades         : {best_result['total_trades']:>10.0f}")
    
    print(f"\n🔌 API ENDPOINTS:")
    # Extract real endpoints from preloaded data stats
    endpoints_info = []
    
    if '_stats' in base_config and 'dataset_details' in base_config['_stats']:
        dataset_details = base_config['_stats']['dataset_details']
        for dataset_name, info in dataset_details.items():
            endpoint = info.get('endpoint')
            rows = info.get('rows', 0)
            if endpoint:
                endpoints_info.append((endpoint, rows))
    
    # Check if intraday stops are enabled
    intraday_stops = base_config.get('intraday_stops', {})
    if intraday_stops.get('enabled', False):
        intraday_endpoint = "/equities/intraday/stock-prices"
        if not any(ep[0] == intraday_endpoint for ep in endpoints_info):
            endpoints_info.append((intraday_endpoint, "on-demand"))
    
    if endpoints_info:
        for idx, (endpoint, rows) in enumerate(endpoints_info, 1):
            if isinstance(rows, int):
                print(f"    {idx}. {endpoint:<45} ({rows:>10,} rows)")
            else:
                print(f"    {idx}. {endpoint:<45} ({rows})")
    else:
        # Fallback to static list if no stats available
        print(f"    1. /equities/eod/options-rawiv")
        print(f"    2. /equities/eod/stock-prices")
        if intraday_stops.get('enabled', False):
            print(f"    3. /equities/intraday/stock-prices")
    
    print("="*120)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # NEW! FULL BACKTEST OF BEST COMBINATION WITH ALL CHARTS
    # ═══════════════════════════════════════════════════════════════════════════
    
    # ✅ Use universal format_params_string() for consistent naming
    best_config_for_naming = base_config.copy()
    best_config_for_naming.update(best_params)
    best_params_str = format_params_string(best_config_for_naming)
    
    # Add SL prefix if provided (from notebook loop)
    sl_prefix = base_config.get('_sl_prefix', '')
    if sl_prefix:
        best_params_str_with_prefix = f"{sl_prefix}_{best_params_str}"
    else:
        best_params_str_with_prefix = best_params_str
    
    print("\n" + "="*80)
    print(" "*15 + "RUNNING FULL BACKTEST FOR BEST COMBINATION")
    print("="*80)
    print("\n📊 Creating detailed report for best combination...")
    print(f"Parameters: {', '.join([f'{k}={v}' for k, v in best_params.items()])}")
    print(f"Files will be saved with prefix: BST_{best_params_str_with_prefix}_*\n")
    
    # Create config for best combination
    best_config = base_config.copy()
    best_config.update(best_params)
    
    if use_legacy_preload:
        best_config['_preloaded_lean_df'] = preloaded_lean_df
        best_config['_preloaded_options_cache'] = preloaded_options_df
    
    # Create folder for best combination with parameters in name
    best_combo_folder = os.path.join(results_folder, f'best_{best_params_str_with_prefix}')
    os.makedirs(best_combo_folder, exist_ok=True)
    
    # Run FULL backtest with ALL charts and exports
    # Note: progress_context=None, so plt.show() will be called but fail due to renderer
    # We'll display charts explicitly afterwards using IPython.display.Image
    best_analyzer = run_backtest(
        strategy_function,
        best_config,
        print_report=True,  # ← SHOW FULL REPORT
        create_charts=True,  # ← CREATE ALL CHARTS
        export_results=True,  # ← EXPORT ALL FILES
        progress_context=None,  # ← Normal mode
        chart_filename=os.path.join(best_combo_folder, f'BST_{best_params_str_with_prefix}_chart.png'),
        export_prefix=os.path.join(best_combo_folder, f'BST_{best_params_str_with_prefix}')
    )
    
    # Save detailed metrics to optimization_metrics.csv
    metrics_data = {
        'metric': list(best_analyzer.metrics.keys()),
        'value': list(best_analyzer.metrics.values())
    }
    metrics_df = pd.DataFrame(metrics_data)
    metrics_path = os.path.join(results_folder, 'optimization_metrics.csv')
    metrics_df.to_csv(metrics_path, index=False)
    
    print(f"\n✓ Detailed metrics saved: {metrics_path}")
    print(f"✓ Best combination results saved to: {best_combo_folder}/")
    print(f"   Files: BST_{best_params_str_with_prefix}_*.csv, BST_{best_params_str_with_prefix}_chart.png")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # DISPLAY CHARTS FOR BEST COMBINATION IN NOTEBOOK
    # ═══════════════════════════════════════════════════════════════════════════
    try:
        # Charts are displayed in the notebook, not here
        chart_file = os.path.join(best_combo_folder, f'BST_{best_params_str_with_prefix}_chart.png')
        if os.path.exists(chart_file):
            print(f"\n📈 Best combination charts saved to: {chart_file}")
    except Exception as e:
        print(f"\n⚠ Could not display charts (saved to {best_combo_folder}/): {e}")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # CREATE OPTIMIZATION COMPARISON CHARTS (save only, display in notebook manually)
    # ═══════════════════════════════════════════════════════════════════════════
    print("\n" + "="*80)
    print(" "*15 + "CREATING OPTIMIZATION COMPARISON CHARTS")
    print("="*80)
    try:
        optimization_chart_path = os.path.join(results_folder, 'optimization_results.png')
        # Save chart but don't display (show_plot=False) - display will be done in notebook for combined results
        plot_optimization_results(
            results_df,
            param_names,
            filename=optimization_chart_path,
            show_plot=False  # Don't display here - will be shown in notebook for combined results
        )
        print(f"✓ Optimization comparison charts saved to: {optimization_chart_path}")
        print("   (Chart will be displayed in notebook for combined results)")
    except Exception as e:
        print(f"⚠ Could not create optimization charts: {e}")
        import traceback
        traceback.print_exc()
    
    print("="*80 + "\n")
    
    return results_df, best_params, results_folder


def plot_optimization_results(results_df, param_names, filename='optimization_results.png', show_plot=True):
    """
    Create visualization of optimization results
    
    Args:
        results_df: Results DataFrame from optimize_parameters()
        param_names: List of parameter names
        filename: Output filename
        show_plot: If True, display plot in Jupyter notebook (default: True)
    """
    import matplotlib.pyplot as plt
    import seaborn as sns
    
    # Handle missing is_valid column (for combined results from multiple optimizations)
    if 'is_valid' not in results_df.columns:
        results_df = results_df.copy()
        results_df['is_valid'] = True
    
    valid_results = results_df[results_df['is_valid'] == True].copy()
    
    if valid_results.empty:
        print("No valid results to plot")
        return
    
    sns.set_style("whitegrid")
    
    fig = plt.figure(figsize=(18, 12))
    
    # 1. Sharpe vs Total Return scatter
    ax1 = plt.subplot(2, 3, 1)
    scatter = ax1.scatter(
        valid_results['total_return'],
        valid_results['sharpe'],
        c=valid_results['max_drawdown'],
        s=valid_results['total_trades']*10,
        alpha=0.6,
        cmap='RdYlGn_r'
    )
    ax1.set_xlabel('Total Return (%)', fontsize=10)
    ax1.set_ylabel('Sharpe Ratio', fontsize=10)
    ax1.set_title('Sharpe vs Return (size=trades, color=drawdown)', fontsize=11, fontweight='bold')
    plt.colorbar(scatter, ax=ax1, label='Max Drawdown (%)')
    ax1.grid(True, alpha=0.3)
    
    # 2. Parameter heatmap (if 2 parameters)
    if len(param_names) == 2:
        ax2 = plt.subplot(2, 3, 2)
        pivot_data = valid_results.pivot_table(
            values='sharpe',
            index=param_names[0],
            columns=param_names[1],
            aggfunc='mean'
        )
        sns.heatmap(pivot_data, annot=True, fmt='.2f', cmap='RdYlGn', ax=ax2)
        ax2.set_title(f'Sharpe Ratio Heatmap', fontsize=11, fontweight='bold')
    else:
        ax2 = plt.subplot(2, 3, 2)
        ax2.text(0.5, 0.5, 'Heatmap requires\nexactly 2 parameters',
                ha='center', va='center', fontsize=12)
        ax2.axis('off')
    
    # 3. Win Rate vs Profit Factor
    ax3 = plt.subplot(2, 3, 3)
    scatter3 = ax3.scatter(
        valid_results['win_rate'],
        valid_results['profit_factor'],
        c=valid_results['sharpe'],
        s=100,
        alpha=0.6,
        cmap='viridis'
    )
    ax3.set_xlabel('Win Rate (%)', fontsize=10)
    ax3.set_ylabel('Profit Factor', fontsize=10)
    ax3.set_title('Win Rate vs Profit Factor (color=Sharpe)', fontsize=11, fontweight='bold')
    plt.colorbar(scatter3, ax=ax3, label='Sharpe Ratio')
    ax3.grid(True, alpha=0.3)
    
    # 4. Distribution of Sharpe Ratios
    ax4 = plt.subplot(2, 3, 4)
    ax4.hist(valid_results['sharpe'], bins=20, color='steelblue', alpha=0.7, edgecolor='black')
    ax4.axvline(valid_results['sharpe'].mean(), color='red', linestyle='--', linewidth=2, label='Mean')
    ax4.axvline(valid_results['sharpe'].median(), color='green', linestyle='--', linewidth=2, label='Median')
    ax4.set_xlabel('Sharpe Ratio', fontsize=10)
    ax4.set_ylabel('Frequency', fontsize=10)
    ax4.set_title('Distribution of Sharpe Ratios', fontsize=11, fontweight='bold')
    ax4.legend()
    ax4.grid(True, alpha=0.3, axis='y')
    
    # 5. Total Trades distribution
    ax5 = plt.subplot(2, 3, 5)
    ax5.hist(valid_results['total_trades'], bins=15, color='coral', alpha=0.7, edgecolor='black')
    ax5.set_xlabel('Total Trades', fontsize=10)
    ax5.set_ylabel('Frequency', fontsize=10)
    ax5.set_title('Distribution of Trade Counts', fontsize=11, fontweight='bold')
    ax5.grid(True, alpha=0.3, axis='y')
    
    # 6. Top 10 combinations
    ax6 = plt.subplot(2, 3, 6)
    if 'combination_id' in valid_results.columns:
        top_10 = valid_results.nlargest(10, 'sharpe')[['combination_id', 'sharpe']].sort_values('sharpe')
        ax6.barh(range(len(top_10)), top_10['sharpe'], color='green', alpha=0.7)
        ax6.set_yticks(range(len(top_10)))
        ax6.set_yticklabels([f"#{int(x)}" for x in top_10['combination_id']])
        ax6.set_xlabel('Sharpe Ratio', fontsize=10)
        ax6.set_title('Top 10 Combinations by Sharpe', fontsize=11, fontweight='bold')
    else:
        # Fallback: use index as combination ID
        top_10 = valid_results.nlargest(10, 'sharpe')['sharpe'].sort_values()
        ax6.barh(range(len(top_10)), top_10.values, color='green', alpha=0.7)
        ax6.set_yticks(range(len(top_10)))
        ax6.set_yticklabels([f"#{i+1}" for i in range(len(top_10))])
        ax6.set_xlabel('Sharpe Ratio', fontsize=10)
        ax6.set_title('Top 10 Combinations by Sharpe', fontsize=11, fontweight='bold')
    ax6.grid(True, alpha=0.3, axis='x')
    
    plt.tight_layout()
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    print(f"\nVisualization saved: {filename}")
    
    # Display plot if requested
    if show_plot:
        try:
            # First try to use IPython.display.Image (most reliable in Jupyter)
            from IPython.display import display, Image
            import os
            if os.path.exists(filename):
                display(Image(filename))
            else:
                # If file doesn't exist yet, try plt.show()
                plt.show()
        except (ImportError, NameError):
            # Not in Jupyter or IPython not available - try plt.show()
            try:
                plt.show()
            except:
                plt.close()
        except Exception:
            # Any other error - try plt.show() as fallback
            try:
                plt.show()
            except:
                plt.close()
    else:
        plt.close()  # Close without displaying


# ============================================================
# CACHE CONFIGURATION (integrated from universal_backend_system.py)
# ============================================================
def get_cache_config(disk_enabled: bool = True, memory_enabled: bool = True, 
                    memory_percent: int = 10, max_age_days: int = 7, 
                    debug: bool = False, cache_dir: str = 'cache',
                    compression: bool = True, auto_cleanup: bool = True) -> Dict[str, Any]:
    """
    Get cache configuration
    
    Args:
        disk_enabled: Enable disk cache
        memory_enabled: Enable memory cache
        memory_percent: RAM percentage for cache (default 10%)
        max_age_days: Maximum cache age in days
        debug: Debug mode
        cache_dir: Cache directory
        compression: Use compression (Parquet + Snappy)
        auto_cleanup: Automatic cleanup of old cache
    
    Returns:
        Dict with cache configuration
    """
    return {
        'disk_enabled': disk_enabled,
        'memory_enabled': memory_enabled,
        'memory_percent': memory_percent,
        'max_age_days': max_age_days,
        'debug': debug,
        'cache_dir': cache_dir,
        'compression': compression,
        'auto_cleanup': auto_cleanup
    }


# ============================================================
# UNIVERSAL CACHE MANAGER (integrated from universal_backend_system.py)
# ============================================================
class UniversalCacheManager:
    """Universal cache manager for any data types"""
    
    # Mapping data types to cache directories
    DATA_TYPE_MAP = {
        'stock_eod': 'STOCK_EOD',
        'stock_intraday': 'STOCK_INTRADAY',
        'options_eod': 'OPTIONS_EOD',
        'options_intraday': 'OPTIONS_INTRADAY',
        # Backward compatibility (old naming):
        'stock': 'STOCK_EOD',
        'options': 'OPTIONS_EOD',
        'intraday': 'OPTIONS_INTRADAY',  # Default intraday = options
    }
    
    def __init__(self, cache_config: Dict[str, Any]):
        self.cache_config = cache_config
        self.disk_enabled = cache_config.get('disk_enabled', True)
        self.memory_enabled = cache_config.get('memory_enabled', True)
        self.memory_percent = cache_config.get('memory_percent', 10)
        self.max_age_days = cache_config.get('max_age_days', 7)
        self.debug = cache_config.get('debug', False)
        self.cache_dir = cache_config.get('cache_dir', 'cache')
        self.compression = cache_config.get('compression', True)
        self.auto_cleanup = cache_config.get('auto_cleanup', True)
        
        # Calculate cache size in RAM
        if self.memory_enabled:
            total_memory = psutil.virtual_memory().total
            self.max_memory_bytes = int(total_memory * self.memory_percent / 100)
            self.memory_cache = {}
            self.cache_order = []
        else:
            self.max_memory_bytes = 0
            self.memory_cache = {}
            self.cache_order = []
        
        # Create cache directories
        if self.disk_enabled:
            os.makedirs(self.cache_dir, exist_ok=True)
    
    def get(self, key: str, data_type: str = 'default') -> Optional[Any]:
        """Get data from cache"""
        try:
            # Check memory
            if self.memory_enabled and key in self.memory_cache:
                if self.debug:
                    print(f"[CACHE] 🧠 Memory hit: {key}")
                return self.memory_cache[key]
            
            # Check disk
            if self.disk_enabled:
                # Map data_type to proper directory structure using DATA_TYPE_MAP
                dir_name = self.DATA_TYPE_MAP.get(data_type, data_type.upper())
                data_dir = f"{self.cache_dir}/{dir_name}"
                
                cache_file = os.path.join(data_dir, f"{key}.parquet")
                if os.path.exists(cache_file):
                    if self._is_cache_valid(cache_file):
                        data = self._load_from_disk(cache_file)
                        if data is not None:
                            # Save to memory
                            if self.memory_enabled:
                                self._save_to_memory(key, data)
                            if self.debug:
                                print(f"[CACHE] 💾 Disk hit: {key}")
                            return data
                
                # NEW: If exact match not found, search for overlapping cache
                # Only for date-range based cache types
                if data_type in ['stock_eod', 'options_eod', 'stock_intraday', 'options_intraday']:
                    overlapping_data = self._find_overlapping_cache(key, data_type, data_dir)
                    if overlapping_data is not None:
                        # Save to memory for fast access
                        if self.memory_enabled:
                            self._save_to_memory(key, overlapping_data)
                        return overlapping_data
            
            if self.debug:
                print(f"[CACHE] ❌ Cache miss: {key}")
            return None
            
        except Exception as e:
            if self.debug:
                print(f"[CACHE] ❌ Error getting {key}: {e}")
            return None
    
    def set(self, key: str, data: Any, data_type: str = 'default') -> bool:
        """Save data to cache"""
        try:
            # Save to memory
            if self.memory_enabled:
                self._save_to_memory(key, data)
            
            # Save to disk
            if self.disk_enabled:
                # Map data_type to proper directory structure using DATA_TYPE_MAP
                dir_name = self.DATA_TYPE_MAP.get(data_type, data_type.upper())
                data_dir = f"{self.cache_dir}/{dir_name}"
                
                # Create directory if it doesn't exist
                os.makedirs(data_dir, exist_ok=True)
                
                cache_file = os.path.join(data_dir, f"{key}.parquet")
                self._save_to_disk(cache_file, data)
            
            if self.debug:
                # Count records for reporting
                record_count = len(data) if hasattr(data, '__len__') else '?'
                print(f"[CACHE] 💾 Saved: {key}")
                print(f"[CACHE] 💾 Saved to cache: {data_type.upper()} ({record_count} records)")
            return True
            
        except Exception as e:
            if self.debug:
                print(f"[CACHE] ❌ Error saving {key}: {e}")
            return False
    
    def _save_to_memory(self, key: str, data: Any):
        """Save to memory with LRU logic"""
        if key in self.memory_cache:
            self.cache_order.remove(key)
        else:
            # Check cache size
            while len(self.memory_cache) > 0 and self._get_memory_usage() > self.max_memory_bytes:
                oldest_key = self.cache_order.pop(0)
                del self.memory_cache[oldest_key]
        
        self.memory_cache[key] = data
        self.cache_order.append(key)
    
    def _save_to_disk(self, file_path: str, data: Any):
        """Save to disk"""
        try:
            # Ensure directory exists
            file_dir = os.path.dirname(file_path)
            if file_dir and not os.path.exists(file_dir):
                os.makedirs(file_dir, exist_ok=True)
            
            if isinstance(data, pd.DataFrame):
                if self.compression:
                    data.to_parquet(file_path, compression='snappy')
                else:
                    data.to_parquet(file_path)
            elif isinstance(data, dict):
                # Convert dict to DataFrame
                df = pd.DataFrame([data])
                if self.compression:
                    df.to_parquet(file_path, compression='snappy')
                else:
                    df.to_parquet(file_path)
            else:
                # Try to convert to DataFrame
                df = pd.DataFrame(data)
                if self.compression:
                    df.to_parquet(file_path, compression='snappy')
                else:
                    df.to_parquet(file_path)
        except Exception as e:
            if self.debug:
                print(f"[CACHE] ❌ Error saving to disk: {e}")
    
    def _load_from_disk(self, file_path: str) -> Optional[Any]:
        """Load from disk"""
        try:
            return pd.read_parquet(file_path)
        except Exception as e:
            if self.debug:
                print(f"[CACHE] ❌ Error loading from disk: {e}")
            return None
    
    def _is_cache_valid(self, file_path: str) -> bool:
        """Check cache validity"""
        if not os.path.exists(file_path):
            return False
        
        file_age = time.time() - os.path.getmtime(file_path)
        max_age_seconds = self.max_age_days * 24 * 3600
        
        return file_age < max_age_seconds
    
    def _get_memory_usage(self) -> int:
        """Get memory usage"""
        total_size = 0
        for key, value in self.memory_cache.items():
            try:
                if hasattr(value, 'memory_usage'):
                    total_size += value.memory_usage(deep=True).sum()
                else:
                    total_size += sys.getsizeof(value)
            except:
                total_size += sys.getsizeof(value)
        return total_size
    
    def _find_overlapping_cache(self, key: str, data_type: str, data_dir: str) -> Optional[Any]:
        """
        Find cache files with overlapping date ranges
        
        Args:
            key: Cache key (format: SYMBOL_START_END or SYMBOL_DATE)
            data_type: Data type (stock_eod, options_eod, etc.)
            data_dir: Cache directory
            
        Returns:
            Filtered data if overlapping cache found, None otherwise
        """
        try:
            import re
            import glob
            from datetime import datetime
            
            # Parse symbol and dates from key
            # Format: "SPY_2024-07-01_2025-10-29" or "SPY_2024-07-01"
            match = re.search(r'^([A-Z]+)_(\d{4}-\d{2}-\d{2})(?:_(\d{4}-\d{2}-\d{2}))?$', key)
            if not match:
                return None
            
            symbol = match.group(1)
            start_date_str = match.group(2)
            end_date_str = match.group(3) if match.group(3) else start_date_str
            
            # Parse dates
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            
            # Find all cache files for this symbol
            if not os.path.exists(data_dir):
                return None
            
            pattern = os.path.join(data_dir, f"{symbol}_*.parquet")
            cache_files = glob.glob(pattern)
            
            if not cache_files:
                return None
            
            # Search for best overlapping cache
            best_match = None
            best_size = float('inf')  # Prefer smallest file that covers range
            
            for cache_file in cache_files:
                # Skip if cache is not valid
                if not self._is_cache_valid(cache_file):
                    continue
                
                # Parse dates from filename
                filename = os.path.basename(cache_file)
                file_match = re.search(r'(\d{4}-\d{2}-\d{2})(?:_(\d{4}-\d{2}-\d{2}))?', filename)
                
                if not file_match:
                    continue
                
                cached_start_str = file_match.group(1)
                cached_end_str = file_match.group(2) if file_match.group(2) else cached_start_str
                
                cached_start = datetime.strptime(cached_start_str, '%Y-%m-%d').date()
                cached_end = datetime.strptime(cached_end_str, '%Y-%m-%d').date()
                
                # Check if cached range CONTAINS requested range
                if cached_start <= start_date and cached_end >= end_date:
                    # Calculate file size (prefer smaller files)
                    file_size = os.path.getsize(cache_file)
                    
                    if file_size < best_size:
                        best_match = cache_file
                        best_size = file_size
            
            if best_match:
                if self.debug:
                    print(f"[CACHE] 🔍 Found overlapping cache: {os.path.basename(best_match)}")
                    print(f"[CACHE]    Requested: {start_date_str} → {end_date_str}")
                    print(f"[CACHE]    Filtering and loading...")
                
                # Load and filter data
                df = pd.read_parquet(best_match)
                
                # Ensure date column is in correct format
                if 'date' in df.columns:
                    if df['date'].dtype == 'object':
                        df['date'] = pd.to_datetime(df['date']).dt.date
                    elif pd.api.types.is_datetime64_any_dtype(df['date']):
                        df['date'] = df['date'].dt.date
                    
                    # Filter by date range
                    filtered = df[(df['date'] >= start_date) & (df['date'] <= end_date)].copy()
                    
                    if self.debug:
                        print(f"[CACHE] ✓ Overlapping cache hit: {len(filtered)} records (filtered from {len(df)})")
                    
                    return filtered
                else:
                    # No date column to filter - return as is
                    if self.debug:
                        print(f"[CACHE] ✓ Overlapping cache hit: {len(df)} records (no date filtering)")
                    return df
            
            return None
            
        except Exception as e:
            if self.debug:
                print(f"[CACHE] ⚠️ Error searching for overlapping cache: {e}")
            return None


# Export all
__all__ = [
    'BacktestResults', 'BacktestAnalyzer', 'ResultsReporter',
    'ChartGenerator', 'ResultsExporter', 'run_backtest', 'run_backtest_with_stoploss',
    'init_api', 'api_call', 'get_api_data', 'is_api_response_valid', 'APIHelper', 'APIManager',
    'ResourceMonitor', 'create_progress_bar', 'update_progress', 'format_time',
    'StopLossManager', 'PositionManager', 'StopLossConfig',
    'calculate_stoploss_metrics', 'print_stoploss_section', 'create_stoploss_charts',
    'create_stoploss_comparison_chart',
    'optimize_parameters', 'plot_optimization_results',
    'create_optimization_folder',
    'preload_options_data',
    'STRATEGIES', 'StrategyRegistry', 'detect_strategy_type', 'format_params_string',
    'preload_data_universal',  # NEW: Universal preloader V2
    'safe_get_greek', 'collect_garbage',  # Helper functions
    'get_option_by_strike_exp',  # NEW: Universal option lookup (works with any endpoint)
    'apply_optimization_preset', 'list_optimization_presets', 
    'calculate_combinations_count', 'print_preset_info',
    'get_cache_config', 'UniversalCacheManager',
    '_process_options_df',
    # Indicator pre-calculation (v2.27.3+)
    'precalculate_indicators_from_config', 'build_indicator_lookup',
    'INDICATOR_REGISTRY', 'auto_calculate_lookback_period',
    # IV Lean / Z-Score functions
    'calculate_iv_lean_from_ivx', 'preload_ivx_zscore_cache'
]


# ============================================================
# OPTIMIZATION PRESET FUNCTIONS
# ============================================================

def apply_optimization_preset(config, preset='default'):
    """
    Apply built-in optimization preset to config
    
    Args:
        config: Configuration dictionary (will be updated)
        preset: Preset name ('default', 'quick_test', 'aggressive', 'conservative')
    
    Returns:
        dict: Updated configuration
    """
    presets = {
        'default': {
            'param_grid': {
                'z_score_entry': [0.8, 1.0, 1.2, 1.5],
                'z_score_exit': [0.05, 0.1, 0.15],
                'lookback_period': [45, 60, 90],
                'dte_target': [30, 45, 60]
            },
            'optimization_metric': 'sharpe',
            'min_trades': 5,
            'max_drawdown_limit': 0.50,
            'parallel': False,
            # 'export_each_combo': True,  # ← Removed, will use from main config
            'results_folder_prefix': 'optimization',
            'chart_filename': 'optimization_analysis.png',
            'show_progress': True,
            'verbose': True
        },
        'quick_test': {
            'param_grid': {
                'z_score_entry': [1.0, 1.5],
                'z_score_exit': [0.1],
                'lookback_period': [60],
                'dte_target': [45]
            },
            'optimization_metric': 'sharpe',
            'min_trades': 3,
            'max_drawdown_limit': 0.40,
            'parallel': False,
            # 'export_each_combo': False,  # ← Removed, will use from main config
            'results_folder_prefix': 'quick_test',
            'chart_filename': 'quick_test_analysis.png',
            'show_progress': True,
            'verbose': False
        },
        'aggressive': {
            'param_grid': {
                'z_score_entry': [1.5, 2.0, 2.5],
                'z_score_exit': [0.05, 0.1],
                'lookback_period': [30, 45, 60],
                'dte_target': [30, 45]
            },
            'optimization_metric': 'total_return',
            'min_trades': 10,
            'max_drawdown_limit': 0.60,
            'parallel': False,
            # 'export_each_combo': True,  # ← Removed, will use from main config
            'results_folder_prefix': 'aggressive',
            'chart_filename': 'aggressive_analysis.png',
            'show_progress': True,
            'verbose': True
        },
        'conservative': {
            'param_grid': {
                'z_score_entry': [0.8, 1.0],
                'z_score_exit': [0.1, 0.15, 0.2],
                'lookback_period': [60, 90, 120],
                'dte_target': [45, 60, 90]
            },
            'optimization_metric': 'calmar',
            'min_trades': 8,
            'max_drawdown_limit': 0.25,
            'parallel': False,
            # 'export_each_combo': True,  # ← Removed, will use from main config
            'results_folder_prefix': 'conservative',
            'chart_filename': 'conservative_analysis.png',
            'show_progress': True,
            'verbose': True
        }
    }
    
    if preset not in presets:
        available = list(presets.keys())
        raise ValueError(f"Preset '{preset}' not found. Available: {available}")
    
    # Update only specific fields from preset
    preset_data = presets[preset]
    
    # CRITICAL LOGIC:
    # - If preset == 'default' → use param_grid from config (if exists)
    # - If preset != 'default' → use param_grid from preset (override config)
    user_param_grid = config.get('param_grid')
    
    fields_to_update = [
        'param_grid', 'min_trades', 'max_drawdown_limit',
        'optimization_metric', 'parallel', 'export_each_combo',
        'results_folder_prefix', 'chart_filename',
        'show_progress', 'verbose'
    ]
    
    for field in fields_to_update:
        if field in preset_data:
            # Special handling for param_grid based on preset type
            if field == 'param_grid':
                if preset == 'default' and user_param_grid is not None:
                    # 'default' preset → preserve user's param_grid
                    continue
                else:
                    # Non-default preset (quick_test, aggressive, etc.) → use preset's param_grid
                    config[field] = preset_data[field]
            else:
                config[field] = preset_data[field]
    
    print(f"✓ Applied preset: {preset}")
    if preset == 'default' and user_param_grid is not None:
        print(f"  (Using user-defined param_grid from config)")
    elif preset != 'default':
        print(f"  (Using param_grid from preset, ignoring config)")
    
    return config


def calculate_combinations_count(param_grid):
    """
    Calculate total number of parameter combinations
    
    Args:
        param_grid: Dictionary with parameter lists
        
    Returns:
        int: Total number of combinations
    """
    import math
    return math.prod(len(values) for values in param_grid.values())


def print_preset_info(config):
    """
    Print preset information and combination count
    
    Args:
        config: Configuration dictionary with preset applied
    """
    preset = config.get('preset', 'unknown')
    combinations = calculate_combinations_count(config['param_grid'])
    
    print(f"\n{'='*60}")
    print(f"OPTIMIZATION PRESET: {preset.upper()}")
    print(f"{'='*60}")
    print(f"Total combinations: {combinations}")
    print(f"Optimization metric: {config.get('optimization_metric', 'sharpe')}")
    print(f"Min trades required: {config.get('min_trades', 10)}")
    print(f"Max drawdown limit: {config.get('max_drawdown_limit', 0.50)}")
    print(f"Parallel execution: {config.get('parallel', True)}")
    print(f"Export each combo: {config.get('export_each_combo', False)}")
    print(f"{'='*60}\n")


def list_optimization_presets():
    """Show available built-in presets"""
    presets = {
        'default': 'Standard configuration (4×3×3×3 = 108 combinations)',
        'quick_test': 'Quick test (2×1×1×1 = 2 combinations)',
        'aggressive': 'Aggressive strategy (3×2×3×2 = 36 combinations)',
        'conservative': 'Conservative strategy (2×3×3×3 = 54 combinations)'
    }
    
    print("\n📋 AVAILABLE OPTIMIZATION PRESETS:")
    print("-" * 60)
    for name, desc in presets.items():
        print(f"  {name:<12} | {desc}")
    print("-" * 60)