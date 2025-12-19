import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import glob
import os
import platform
import json # New import

# Font configuration
import matplotlib.font_manager as fm

# Try to set Pretendard if available, else fallback
fonts = [f.name for f in fm.fontManager.ttflist]
if 'Pretendard' in fonts:
    plt.rc('font', family='Pretendard')
elif 'Pretendard JP' in fonts:
    plt.rc('font', family='Pretendard JP')
else:
    # Fallback logic
    if system_name == 'Windows':
        plt.rc('font', family='Malgun Gothic')
    elif system_name == 'Darwin':
        plt.rc('font', family='AppleGothic')
    else:
        plt.rc('font', family='NanumGothic')

plt.rc('axes', unicode_minus=False)

def load_and_merge_data(file_patterns):
    files = []
    for pattern in file_patterns:
        files.extend(glob.glob(pattern))
    
    dfs = []
    for f in files:
        try:
            # Renewable energy data usually comes in cp949 or euc-kr
            df = pd.read_csv(f, encoding='cp949') 
            dfs.append(df)
            print(f"Loaded {f} with shape {df.shape}")
        except Exception as e:
            print(f"Error loading {f}: {e}")
    
    if not dfs:
        raise ValueError("No files loaded.")
    
    combined_df = pd.concat(dfs, ignore_index=True)
    return combined_df

def clean_data(df):
    print("\nInitial Columns:", df.columns.tolist())
    
    # Filter for Incheon (assuming column '광역지자체' exists based on preview)
    # The snippet showed '광역지자체'
    if '광역지자체' in df.columns:
        df_incheon = df[df['광역지자체'] == '인천'].copy()
    else:
        print("Warning: '광역지자체' column not found. Using full dataset.")
        df_incheon = df.copy()

    # Numeric conversion
    # Columns typically: 연도, 광역지자체, 기초지자체, 태양광, 풍력, etc.
    # Values often have commas like "1,234" or "-" for 0/NaN.
    
    # Identify value columns (exclude metadata columns)
    # Exclude metadata AND aggregate columns to prevent double counting
    # Exclude metadata AND aggregate columns to prevent double counting
    exclude_cols = ['연도', '광역지자체', '기초지자체', '신재생에너지 합계', '재생에너지합계', '신에너지합계', '재생에너지 합계', '신에너지 합계', '합계', '소계', '지역별 공급비중']
    value_cols = [c for c in df.columns if c not in exclude_cols]
    
    for col in value_cols:
        # Remove commas and handle '-'
        df_incheon[col] = df_incheon[col].astype(str).str.replace(',', '').str.strip()
        df_incheon[col] = df_incheon[col].replace(['-', ''], '0')
        # Convert to float
        df_incheon[col] = pd.to_numeric(df_incheon[col], errors='coerce').fillna(0)
            
    return df_incheon

def plot_yearly_trend(df):
    # Sum all energy sources by year
    # Assuming '합계' column might exist, or we sum all value columns
    # Exclude metadata AND aggregate columns to prevent double counting
    # Exclude metadata AND aggregate columns to prevent double counting
    exclude_cols = ['연도', '광역지자체', '기초지자체', '신재생에너지 합계', '재생에너지합계', '신에너지합계', '재생에너지 합계', '신에너지 합계', '합계', '소계', '지역별 공급비중']
    value_cols = [c for c in df.columns if c not in exclude_cols]
    
    # Group by Year
    yearly_sum = df.groupby('연도')[value_cols].sum().sum(axis=1).reset_index(name='Total_Generation')
    
    plt.figure(figsize=(10, 6))
    
    # Ensure years are sorted
    yearly_sum = yearly_sum.sort_values('연도')
    
    sns.lineplot(data=yearly_sum, x='연도', y='Total_Generation', marker='o', linewidth=3, color='steelblue')
    plt.ylim(0, 700000) 
    
    # Force integer ticks for years
    plt.xticks(yearly_sum['연도'].astype(int))
    
    # Add value labels
    # Add value labels
    for x, y in zip(yearly_sum['연도'], yearly_sum['Total_Generation']):
        plt.text(x, y + (y*0.02), f'{y:,.0f}', ha='center', va='bottom', fontsize=16, fontweight='bold')

    plt.title('인천시 연도별 신재생에너지 총 발전량 추이', fontsize=24, pad=20, fontweight='bold')
    plt.xlabel('연도', fontsize=16, fontweight='bold')
    plt.ylabel('발전량 (MWh)', fontsize=16, fontweight='bold')
    plt.xticks(fontsize=14)
    plt.yticks(fontsize=14)
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig('yearly_trend.png', dpi=300)
    print("Saved yearly_trend.png")

def plot_yearly_trend_by_source(df):
    # Exclude metadata AND aggregate columns to prevent double counting
    # Exclude metadata AND aggregate columns to prevent double counting
    exclude_cols = ['연도', '광역지자체', '기초지자체', '신재생에너지 합계', '재생에너지합계', '신에너지합계', '재생에너지 합계', '신에너지 합계', '합계', '소계', '지역별 공급비중']
    value_cols = [c for c in df.columns if c not in exclude_cols]
    
    # Group by Year and Source (melt or simple sum)
    yearly_source = df.groupby('연도')[value_cols].sum()
    yearly_source = yearly_source.sort_index() # Sort by Year
    
    plt.figure(figsize=(12, 7))
    yearly_source.plot(kind='area', stacked=True, colormap='tab20', alpha=0.8, figsize=(12, 7))
    
    plt.xticks(yearly_source.index.astype(int), fontsize=14) # Integer ticks
    plt.yticks(fontsize=14)
    
    plt.title('인천시 연도별 신재생에너지 원별 발전량 추이 (Stacked Area)', fontsize=24, pad=20, fontweight='bold')
    plt.xlabel('연도', fontsize=16, fontweight='bold')
    plt.ylabel('발전량 (MWh)', fontsize=16, fontweight='bold')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=14)
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig('yearly_trend_by_source.png', dpi=300)
    print("Saved yearly_trend_by_source.png")

def plot_regional_comparison(df):
    # Latest year only for comparison
    latest_year = df['연도'].max()
    df_latest = df[df['연도'] == latest_year]
    
    # Exclude metadata AND aggregate columns to prevent double counting
    # Exclude metadata AND aggregate columns to prevent double counting
    exclude_cols = ['연도', '광역지자체', '기초지자체', '신재생에너지 합계', '재생에너지합계', '신에너지합계', '재생에너지 합계', '신에너지 합계', '합계', '소계', '지역별 공급비중']
    value_cols = [c for c in df.columns if c not in exclude_cols]
    
    # Group by Region (Gun/Gu)
    regional_sum = df_latest.groupby('기초지자체')[value_cols].sum().sum(axis=1).reset_index(name='Total_Generation')
    regional_sum = regional_sum.sort_values('Total_Generation', ascending=False)
    
    plt.figure(figsize=(12, 6))
    sns.barplot(data=regional_sum, x='기초지자체', y='Total_Generation', palette='viridis')
    plt.title(f'인천시 지역별 신재생에너지 발전량 비교 ({latest_year})', fontsize=24, pad=20, fontweight='bold')
    plt.xlabel('지역 (군·구)', fontsize=16, fontweight='bold')
    plt.ylabel('발전량 (MWh)', fontsize=16, fontweight='bold')
    plt.xticks(rotation=45, fontsize=14)
    plt.yticks(fontsize=14)
    plt.tight_layout()
    plt.savefig('regional_comparison.png', dpi=300)
    print("Saved regional_comparison.png")

def plot_regional_source_breakdown(df):
    latest_year = df['연도'].max()
    df_latest = df[df['연도'] == latest_year]
    
    # Exclude metadata AND aggregate columns to prevent double counting
    # Exclude metadata AND aggregate columns to prevent double counting
    exclude_cols = ['연도', '광역지자체', '기초지자체', '신재생에너지 합계', '재생에너지합계', '신에너지합계', '재생에너지 합계', '신에너지 합계', '합계', '소계', '지역별 공급비중']
    value_cols = [c for c in df.columns if c not in exclude_cols]
    
    # Stacked bar chart: x=Region, y=Generation, stack=Source
    regional_source = df_latest.groupby('기초지자체')[value_cols].sum()
    # Sort by total generation
    regional_source['Total'] = regional_source.sum(axis=1)
    regional_source = regional_source.sort_values('Total', ascending=False).drop(columns='Total')
    
    plt.figure(figsize=(14, 8))
    # Use distinct colormap
    regional_source.plot(kind='bar', stacked=True, colormap='tab20', width=0.8, figsize=(14, 8))
    plt.title(f'인천시 지역별/원별 신재생에너지 발전량 ({latest_year})', fontsize=24, pad=20, fontweight='bold')
    plt.xlabel('지역 (군·구)', fontsize=16, fontweight='bold')
    plt.ylabel('발전량 (MWh)', fontsize=16, fontweight='bold')
    plt.xticks(rotation=45, fontsize=14)
    plt.yticks(fontsize=14)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=14)
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig('regional_source_breakdown.png', dpi=300)
    print("Saved regional_source_breakdown.png")

def plot_energy_mix(df):
    # Total accumulation or Latest year
    latest_year = df['연도'].max()
    df_latest = df[df['연도'] == latest_year]
    
    exclude_cols = ['연도', '광역지자체', '기초지자체', '신재생에너지 합계', '재생에너지합계', '신에너지합계', '재생에너지 합계', '신에너지 합계', '합계', '소계', '지역별 공급비중'] # potential aggregate cols
    value_cols = [c for c in df.columns if c not in exclude_cols]
    
    total_mix = df_latest[value_cols].sum().sort_values(ascending=False)
    
    # Filter out zero values
    total_mix = total_mix[total_mix > 0]
    
    # Group small percentages into "Others" to prevent overlap
    threshold = 0.02 # 2%
    total_sum = total_mix.sum()
    mask = total_mix / total_sum >= threshold
    
    large_mix = total_mix[mask]
    small_mix = total_mix[~mask]
    
    if not small_mix.empty:
        large_mix['기타 (Others)'] = small_mix.sum()
    
    large_mix = large_mix.sort_values(ascending=False)
    
    plt.figure(figsize=(14, 8))
    # Remove text labels from chart to fix overlapping
    wedges, texts, autotexts = plt.pie(
        large_mix, 
        labels=None, # No labels on chart
        autopct='%1.1f%%', 
        pctdistance=0.85,
        startangle=140, 
        colors=sns.color_palette('pastel')
    )
    
    # Add Legend
    plt.legend(
        wedges, 
        large_mix.index,
        title="에너지원",
        loc="center left",
        bbox_to_anchor=(1, 0, 0.5, 1),
        fontsize=14,
        title_fontsize=16
    )
    
    plt.title(f'인천시 신재생에너지 원별 구성비 ({latest_year})', fontsize=24, fontweight='bold')
    plt.axis('equal')
    plt.tight_layout()
    plt.savefig('energy_mix.png', dpi=300)
    print("Saved energy_mix.png")

def plot_heatmap(df):
    latest_year = df['연도'].max()
    df_latest = df[df['연도'] == latest_year]
    
    # Exclude metadata AND aggregate columns to prevent double counting
    # Exclude metadata AND aggregate columns to prevent double counting
    exclude_cols = ['연도', '광역지자체', '기초지자체', '신재생에너지 합계', '재생에너지합계', '신에너지합계', '재생에너지 합계', '신에너지 합계', '합계', '소계', '지역별 공급비중']
    value_cols = [c for c in df.columns if c not in exclude_cols]
    
    # Group by Region and Source
    heatmap_data = df_latest.groupby('기초지자체')[value_cols].sum()
    
    plt.figure(figsize=(14, 10))
    sns.heatmap(heatmap_data, annot=True, fmt=',.0f', cmap='YlGnBu', annot_kws={"size": 12})
    plt.title(f'인천시 지역별/원별 발전량 히트맵 ({latest_year})', fontsize=24, pad=20, fontweight='bold')
    plt.xlabel('에너지원', fontsize=16, fontweight='bold')
    plt.ylabel('지역 (군·구)', fontsize=16, fontweight='bold')
    plt.xticks(fontsize=14)
    plt.yticks(fontsize=14)
    plt.tight_layout()
    plt.savefig('heatmap.png', dpi=300)
    print("Saved heatmap.png")

def plot_yoy_growth(df):
    # Exclude metadata AND aggregate columns to prevent double counting
    # Exclude metadata AND aggregate columns to prevent double counting
    exclude_cols = ['연도', '광역지자체', '기초지자체', '신재생에너지 합계', '재생에너지합계', '신에너지합계', '재생에너지 합계', '신에너지 합계', '합계', '소계', '지역별 공급비중']
    value_cols = [c for c in df.columns if c not in exclude_cols]
    
    yearly_total = df.groupby('연도')[value_cols].sum().sum(axis=1).sort_index()
    growth_rate = yearly_total.pct_change() * 100
    
    # Drop NaN (first year)
    growth_rate = growth_rate.dropna()
    
    plt.figure(figsize=(10, 6))
    if not growth_rate.empty:
        bars = plt.bar(growth_rate.index.astype(str), growth_rate.values, color='lightgreen')
        
        plt.title('인천시 신재생에너지 전년 대비 성장률 (YoY)', fontsize=24, pad=20, fontweight='bold')
        plt.xlabel('연도', fontsize=16, fontweight='bold')
        plt.ylabel('성장률 (%)', fontsize=16, fontweight='bold')
        plt.xticks(fontsize=14)
        plt.yticks(fontsize=14)
        
        # Annotate
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height,
                     f'{height:.1f}%',
                     ha='center', va='bottom', fontsize=14, fontweight='bold')
        
        plt.axhline(0, color='black', linewidth=0.8)
        plt.grid(axis='y', linestyle='--', alpha=0.5)
        plt.tight_layout()
        plt.savefig('yoy_growth.png', dpi=300)
        print("Saved yoy_growth.png")
    else:
        print("Not enough data for YoY growth analysis.")

def plot_top_solar_districts(df):
    latest_year = df['연도'].max()
    df_latest = df[df['연도'] == latest_year]
    
    # Check if Solar exists (usually '태양광')
    solar_col = [c for c in df.columns if '태양광' in c]
    if not solar_col:
        print("Solar column not found.")
        return
    
    solar_col = solar_col[0]
    
    top_districts = df_latest.groupby('기초지자체')[solar_col].sum().sort_values(ascending=False)
    
    plt.figure(figsize=(12, 6))
    sns.barplot(x=top_districts.index, y=top_districts.values, palette='Oranges_r')
    plt.title(f'인천시 태양광 발전 상위 지역 ({latest_year})', fontsize=24, pad=20, fontweight='bold')
    plt.xlabel('지역 (군·구)', fontsize=16, fontweight='bold')
    plt.ylabel('발전량 (MWh)', fontsize=16, fontweight='bold')
    plt.xticks(rotation=45, fontsize=14)
    plt.yticks(fontsize=14)
    plt.tight_layout()
    plt.savefig('top_districts_solar.png', dpi=300)
    print("Saved top_districts_solar.png")

def plot_solar_vs_others(df):
    latest_year = df['연도'].max()
    df_latest = df[df['연도'] == latest_year]
    
    # Exclude metadata AND aggregate columns to prevent double counting
    # Exclude metadata AND aggregate columns to prevent double counting
    exclude_cols = ['연도', '광역지자체', '기초지자체', '신재생에너지 합계', '재생에너지합계', '신에너지합계', '재생에너지 합계', '신에너지 합계', '합계', '소계', '지역별 공급비중']
    value_cols = [c for c in df.columns if c not in exclude_cols]
    
    total_mix = df_latest[value_cols].sum()
    
    solar_col = [c for c in df.columns if '태양광' in c]
    if solar_col:
        solar_val = total_mix[solar_col[0]]
        others_val = total_mix.sum() - solar_val
        
        plt.figure(figsize=(8, 8))
        plt.pie([solar_val, others_val], labels=['태양광 (Solar)', '기타 (Others)'], autopct='%1.1f%%', 
                startangle=90, colors=['orange', 'lightgray'], textprops={'fontsize': 16, 'fontweight': 'bold'})
        plt.title(f'태양광 vs 기타 에너지 비중 ({latest_year})', fontsize=24, fontweight='bold')
        plt.tight_layout()
        plt.savefig('solar_vs_others.png', dpi=300)
        print("Saved solar_vs_others.png")


def export_dashboard_data(df):
    # Prepare data structures for Chart.js
    
    # Exclude metadata AND aggregate columns to prevent double counting
    # Exclude metadata AND aggregate columns to prevent double counting
    exclude_cols = ['연도', '광역지자체', '기초지자체', '신재생에너지 합계', '재생에너지합계', '신에너지합계', '재생에너지 합계', '신에너지 합계', '합계', '소계', '지역별 공급비중']
    value_cols = [c for c in df.columns if c not in exclude_cols]
    
    # 1. Yearly Trend
    yearly_df = df.groupby('연도')[value_cols].sum()
    yearly_data = []
    for year in yearly_df.index:
        row = {"year": int(year)}
        row.update(yearly_df.loc[year].to_dict())
        yearly_data.append(row)
        
    # 2. Regional Data (All Years)
    years = sorted(df['연도'].unique())
    regional_data_by_year = {}
    
    for year in years:
        df_year = df[df['연도'] == year]
        regional_df = df_year.groupby('기초지자체')[value_cols].sum()
        regional_data = []
        for region in regional_df.index:
            row = {"region": region}
            row.update(regional_df.loc[region].to_dict())
            regional_data.append(row)
        regional_data_by_year[int(year)] = regional_data
        
    # 3. Source List
    sources = value_cols
    
    # 4. YoY Growth Rate
    yearly_total = df.groupby('연도')[value_cols].sum().sum(axis=1).sort_index()
    growth_rate = yearly_total.pct_change() * 100
    growth_data = []
    for year in growth_rate.index:
        if not pd.isna(growth_rate[year]):
             growth_data.append({"year": int(year), "rate": round(growth_rate[year], 1)})
    
    latest_year = df['연도'].max()
    dashboard_data = {
        "latest_year": int(latest_year),
        "yearly": yearly_data,
        "regional": regional_data_by_year, # Changed structure
        "sources": sources,
        "growth_rate": growth_data
    }
    
    with open("dashboard_data.json", "w", encoding='utf-8') as f:
        json.dump(dashboard_data, f, ensure_ascii=False, indent=4)
    print("Saved dashboard_data.json")

def main():
    base_dir = r"c:\Users\User\Downloads\프로젝트"
    file_patterns = [os.path.join(base_dir, "202512190938_테스트*.CSV")]
    
    print("Loading data...")
    df = load_and_merge_data(file_patterns)
    
    print("Cleaning data...")
    df_clean = clean_data(df)
    
    print(f"Filtered Data (Incheon): {df_clean.shape}")
    print(df_clean.head())
    
    # Create output directory if needed or just save in current
    os.chdir(base_dir) # Switch to project dir for saving output
    
    print("Generating visualizations...")
    try:
        plot_yearly_trend(df_clean)
        plot_yearly_trend_by_source(df_clean) 
        plot_regional_comparison(df_clean)
        plot_regional_source_breakdown(df_clean) 
        plot_energy_mix(df_clean)
        
        # New Deep Analysis
        plot_heatmap(df_clean)
        plot_yoy_growth(df_clean)
        plot_top_solar_districts(df_clean)
        plot_solar_vs_others(df_clean)
        
        # Export for Web
        export_dashboard_data(df_clean)
        
    except Exception as e:
        print(f"Error during plotting: {e}")
        import traceback
        traceback.print_exc()

    # Save cleaned data
    df_clean.to_csv("incheon_renewable_data_cleaned.csv", index=False, encoding='cp949') # cp949 for Excel compatibility in KR
    print("Saved incheon_renewable_data_cleaned.csv")

if __name__ == "__main__":
    main()
