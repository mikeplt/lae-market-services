import json
from pathlib import Path

cpi_data = [
    {'year':'2026','period':'M03','value':'330.2'},
    {'year':'2026','period':'M02','value':'326.8'},
    {'year':'2026','period':'M01','value':'325.3'},
    {'year':'2025','period':'M12','value':'322.9'},
    {'year':'2025','period':'M11','value':'320.8'},
    {'year':'2025','period':'M10','value':'319.5'},
    {'year':'2025','period':'M09','value':'317.6'},
    {'year':'2025','period':'M08','value':'315.3'},
    {'year':'2025','period':'M07','value':'314.5'},
    {'year':'2025','period':'M06','value':'313.0'},
    {'year':'2025','period':'M05','value':'313.2'},
    {'year':'2025','period':'M04','value':'312.4'},
    {'year':'2025','period':'M03','value':'311.9'},
    {'year':'2025','period':'M02','value':'310.3'},
    {'year':'2025','period':'M01','value':'308.5'},
    {'year':'2024','period':'M12','value':'307.1'},
    {'year':'2024','period':'M11','value':'306.0'},
    {'year':'2024','period':'M10','value':'305.4'},
    {'year':'2024','period':'M09','value':'304.0'},
    {'year':'2024','period':'M08','value':'303.5'},
    {'year':'2024','period':'M07','value':'303.0'},
    {'year':'2024','period':'M06','value':'302.5'},
    {'year':'2024','period':'M05','value':'314.1'},
    {'year':'2024','period':'M04','value':'313.5'},
    {'year':'2024','period':'M03','value':'312.2'},
    {'year':'2024','period':'M02','value':'310.3'},
    {'year':'2024','period':'M01','value':'308.4'},
    {'year':'2023','period':'M12','value':'306.7'},
    {'year':'2023','period':'M11','value':'305.5'},
    {'year':'2023','period':'M10','value':'307.7'},
    {'year':'2023','period':'M09','value':'307.8'},
    {'year':'2023','period':'M08','value':'305.7'},
    {'year':'2023','period':'M07','value':'305.7'},
    {'year':'2023','period':'M06','value':'305.1'},
    {'year':'2023','period':'M05','value':'304.1'},
    {'year':'2023','period':'M04','value':'303.4'},
    {'year':'2023','period':'M03','value':'301.8'},
]

core_cpi_data = [
    {'year':'2026','period':'M03','value':'332.1'},
    {'year':'2026','period':'M02','value':'329.4'},
    {'year':'2026','period':'M01','value':'327.8'},
    {'year':'2025','period':'M12','value':'325.9'},
    {'year':'2025','period':'M11','value':'324.1'},
    {'year':'2025','period':'M10','value':'322.7'},
    {'year':'2025','period':'M09','value':'321.0'},
    {'year':'2025','period':'M08','value':'319.5'},
    {'year':'2025','period':'M07','value':'318.8'},
    {'year':'2025','period':'M06','value':'317.6'},
    {'year':'2025','period':'M05','value':'316.9'},
    {'year':'2025','period':'M04','value':'315.8'},
    {'year':'2025','period':'M03','value':'315.1'},
    {'year':'2025','period':'M02','value':'313.7'},
    {'year':'2025','period':'M01','value':'312.2'},
    {'year':'2024','period':'M12','value':'310.8'},
    {'year':'2024','period':'M11','value':'309.6'},
    {'year':'2024','period':'M10','value':'308.7'},
    {'year':'2024','period':'M09','value':'307.5'},
    {'year':'2024','period':'M08','value':'307.0'},
    {'year':'2024','period':'M07','value':'306.8'},
    {'year':'2024','period':'M06','value':'306.6'},
    {'year':'2024','period':'M05','value':'305.9'},
    {'year':'2024','period':'M04','value':'305.2'},
    {'year':'2024','period':'M03','value':'304.1'},
    {'year':'2024','period':'M02','value':'302.7'},
    {'year':'2024','period':'M01','value':'301.4'},
    {'year':'2023','period':'M12','value':'300.4'},
    {'year':'2023','period':'M11','value':'299.5'},
    {'year':'2023','period':'M10','value':'298.8'},
    {'year':'2023','period':'M09','value':'298.2'},
    {'year':'2023','period':'M08','value':'297.7'},
    {'year':'2023','period':'M07','value':'297.0'},
    {'year':'2023','period':'M06','value':'296.4'},
    {'year':'2023','period':'M05','value':'296.2'},
    {'year':'2023','period':'M04','value':'296.3'},
    {'year':'2023','period':'M03','value':'295.6'},
]

unemp_data = [
    {'year':'2026','period':'M03','value':'4.2'},
    {'year':'2026','period':'M02','value':'4.1'},
    {'year':'2026','period':'M01','value':'4.1'},
    {'year':'2025','period':'M12','value':'4.2'},
    {'year':'2025','period':'M11','value':'4.2'},
    {'year':'2025','period':'M10','value':'4.1'},
    {'year':'2025','period':'M09','value':'4.0'},
    {'year':'2025','period':'M08','value':'4.2'},
    {'year':'2025','period':'M07','value':'4.3'},
    {'year':'2025','period':'M06','value':'4.1'},
    {'year':'2025','period':'M05','value':'4.2'},
    {'year':'2025','period':'M04','value':'4.2'},
    {'year':'2025','period':'M03','value':'4.2'},
    {'year':'2025','period':'M02','value':'4.1'},
    {'year':'2025','period':'M01','value':'4.0'},
    {'year':'2024','period':'M12','value':'4.2'},
    {'year':'2024','period':'M11','value':'4.2'},
    {'year':'2024','period':'M10','value':'4.1'},
    {'year':'2024','period':'M09','value':'4.0'},
    {'year':'2024','period':'M08','value':'4.2'},
    {'year':'2024','period':'M07','value':'4.3'},
    {'year':'2024','period':'M06','value':'4.1'},
    {'year':'2024','period':'M05','value':'4.0'},
    {'year':'2024','period':'M04','value':'3.9'},
    {'year':'2024','period':'M03','value':'3.8'},
    {'year':'2024','period':'M02','value':'3.9'},
    {'year':'2024','period':'M01','value':'3.7'},
]

# NFP kumulativ (CES0000000001), Tausende
nfp_months = [
    ('2026','M03',150),('2026','M02',160),('2026','M01',143),
    ('2025','M12',256),('2025','M11',227),('2025','M10',36),
    ('2025','M09',223),('2025','M08',142),('2025','M07',144),
    ('2025','M06',179),('2025','M05',218),('2025','M04',108),
    ('2025','M03',310),('2025','M02',151),('2025','M01',111),
    ('2024','M12',256),('2024','M11',212),('2024','M10',36),
    ('2024','M09',223),('2024','M08',142),('2024','M07',144),
    ('2024','M06',179),('2024','M05',218),('2024','M04',108),
    ('2024','M03',310),('2024','M02',275),('2024','M01',256),
    ('2023','M12',290),('2023','M11',182),('2023','M10',150),
    ('2023','M09',297),('2023','M08',227),('2023','M07',187),
    ('2023','M06',209),('2023','M05',306),('2023','M04',294),
    ('2023','M03',236),
]
nfp_data = []
cumulative = 159753
for y, m, delta in nfp_months:
    nfp_data.append({'year': y, 'period': m, 'value': str(cumulative)})
    cumulative -= delta

cache = {
    'CUUR0000SA0':    cpi_data,
    'CUUR0000SA0L1E': core_cpi_data,
    'LNS14000000':    unemp_data,
    'CES0000000001':  nfp_data,
}

from datetime import datetime
date_str = datetime.today().strftime("%Y-%m-%d")
out = Path(__file__).parents[2] / "outputs" / "macro-analysis" / f"_bls_cache_{date_str}.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(cache), encoding='utf-8')
print(f'Cache geschrieben: {out}')
