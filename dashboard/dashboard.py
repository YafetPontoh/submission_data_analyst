from typing import Tuple
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from babel.numbers import format_currency
import os


# load_data() untuk memanggil data
def load_data() -> pd.DataFrame:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(current_dir, 'all_data.csv')
    df = pd.read_csv(csv_path)
    date_columns = ['order_purchase_timestamp', 'order_approved_at', 'order_delivered_carrier_date',
                    'order_delivered_customer_date', 'order_estimated_delivery_date']
    for column in date_columns:
        df[column] = pd.to_datetime(df[column])
    return df


# Fungsi untuk membuat daily_orders
def create_time_based_df(df: pd.DataFrame, rule: str) -> pd.DataFrame:
    time_based_df = df.resample(rule=rule, on='order_purchase_timestamp').agg({
        'order_id': 'nunique',
        'payment_value': 'sum'
    })
    return time_based_df.reset_index()


# Fungsi untuk membuat sidebar
def create_sidebar(df: pd.DataFrame) -> Tuple[pd.Timestamp, pd.Timestamp, str]:
    with st.sidebar:
        min_date = df['order_purchase_timestamp'].min().date()
        max_date = df['order_purchase_timestamp'].max().date()

        start_date, end_date = st.date_input(
            label='Rentang Waktu', min_value=min_date, max_value=max_date,
            value=[min_date, max_date]
        )

        order_status = ['ALL'] + list(df['order_status'].unique())
        select_status = st.radio('Pilih Order Status: ', order_status)

    return pd.Timestamp(start_date), pd.Timestamp(end_date), select_status


# Fungsi untuk memfilter data
def filter_data(df: pd.DataFrame, start_date: pd.Timestamp, end_date: pd.Timestamp, select_status: str) -> pd.DataFrame:
    filtered_df = df[(df["order_purchase_timestamp"].dt.date >= start_date.date()) &
                     (df["order_purchase_timestamp"].dt.date <= end_date.date())]

    if select_status != 'ALL':
        filtered_df = filtered_df[filtered_df['order_status'] == select_status]

    return filtered_df


# Fungsi untuk membuat top 5 best and worst
def create_best_worst_category_df(df: pd.DataFrame) -> pd.DataFrame:
    products_visualization = df.groupby('product_category_name_english')['qty_order'].sum().reset_index()
    return products_visualization


# Fungsi untuk membuat RFM Analysis
def rfm_anaysis_df(df: pd.DataFrame) -> pd.DataFrame:
    now = df['order_purchase_timestamp'].max()
    rfm_df = df.groupby(by='customer_id', as_index=False).agg({
        'order_purchase_timestamp': lambda x: (now - x.max()).days,
        'order_id': 'count',
        'payment_value': 'sum'
    })
    rfm_df.columns = ['customer_id', 'recency', 'frequency', 'monetary']
    rfm_df['numeric_id'] = pd.factorize(rfm_df['customer_id'])[0] + 1

    return rfm_df


# Fungsi untuk Membuat Geoanalysis
def geoanalyze_df(df: pd.DataFrame) -> pd.Series:
    sales_by_state = df.groupby('customer_state')['payment_value'].sum().sort_values(ascending=True)

    return sales_by_state


# Fungsi untuk menampilkan grafik pesanan bulanan
def plot_time_based_orders(df: pd.DataFrame, time_rule: str, title: str):
    time_based_df = create_time_based_df(df, time_rule)

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(time_based_df['order_purchase_timestamp'], time_based_df['order_id'])
    ax.set_title(title)
    ax.set_xlabel('Date')
    ax.set_ylabel('Number of Orders')
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format_currency(x, 'BRL', locale='pt_BR')))

    st.pyplot(fig)


# Fungsi untuk menampilkan top 5 best and worst
def create_best_worst_category(df: pd.DataFrame):
    products_visualization_df = create_best_worst_category_df(df)

    fig, ax = plt.subplots(nrows=2, ncols=1, figsize=(16, 12))

    colors = ["#72BCD4", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]

    for i, order in enumerate(['descending', 'ascending']):
        sns.barplot(x='qty_order', y='product_category_name_english',
                    data=products_visualization_df.sort_values(
                        by='qty_order', ascending=(order == 'ascending')
                    ).head(5),
                    palette=colors, ax=ax[i])
        ax[i].set_xlabel('Total Quantity Orders')
        ax[i].set_ylabel('Product Category Name')
        ax[i].set_title(f'Top 5 {"Best" if order == "descending" else "Worst"} Selling Product Categories',
                        loc='center', fontsize=15)
        ax[i].tick_params(axis='y', labelsize=12)

    st.subheader('Top 5 Kategori Penjualan Product Terbaik dan Terburuk Berdasarkan Quantity Order')
    st.pyplot(fig)


# Fungsi untuk menampilkan rfm
def rfm_analysis(df: pd.DataFrame):
    rfm_df = rfm_anaysis_df(df)

    fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(30, 6))
    colors = ['#72BCD4', '#72BCD4', '#72BCD4', '#72BCD4', '#72BCD4']

    metrics = ['recency', 'frequency', 'monetary']
    titles = ['Last Purchase (days)', 'Purchase Frequency', 'Total Spent']

    for i, metric in enumerate(metrics):
        order = 'ascending' if metric == 'recency' else 'descending'
        sns.barplot(y=metric, x='numeric_id',
                    data=rfm_df.sort_values(by=metric, ascending=(order == 'ascending')).head(5),
                    palette=colors, ax=ax[i])
        ax[i].set_ylabel(None)
        ax[i].set_xlabel(None)
        ax[i].set_title(titles[i], loc='center', fontsize=18)
        ax[i].tick_params(axis='x', labelsize=15)

        if metric == 'monetary':
            ax[i].yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format_currency(x, 'BRL', locale='pt_BR')))

    st.subheader('Best Customers Based on RFM Parameters')
    st.pyplot(fig)


# Fungsi untuk menampilkan Geoanalysis
def geoanalyze(df: pd.DataFrame):
    all_df = geoanalyze_df(df)

    fig, ax = plt.subplots(figsize=(12, 6))
    all_df.plot(kind='barh', ax=ax)
    plt.title('Total Penjualan berdasarkan Negara Bagian')
    plt.ylabel('Negara Bagian')
    plt.xlabel('Total Penjualan')
    plt.tight_layout()
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format_currency(x, 'BRL', locale='pt_BR')))

    st.subheader('Total Penjualan berdasarkan Negara Bagian')
    st.pyplot(fig)


# Fungsi untuk menampilkan clustering
def clustering(df):
    fig, ax = plt.subplots(figsize=(14, 8))

    scatter = ax.scatter(df['price'], df['freight_value'], c=df['review_score'], cmap='viridis', alpha=0.5)
    plt.colorbar(scatter, label='Skor Review')

    plt.xlabel('Harga Produk')
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format_currency(x, 'BRL', locale='pt_BR')))

    plt.ylabel('Biaya Pengiriman')
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format_currency(x, 'BRL', locale='pt_BR')))

    st.subheader('Hubungan antara Harga, Biaya Pengiriman, dan Skor Review')
    st.pyplot(fig)


# Fungsi untuk menampilkan statistik pesanan
def create_order_stats(df: pd.DataFrame):
    col1, col2 = st.columns(2)

    total_orders = df['order_id'].nunique()
    total_revenue = df['payment_value'].sum()

    with col1:
        st.metric('Total Orders', total_orders)

    with col2:
        formatted_revenue = format_currency(total_revenue, 'BRL', locale='pt_BR')
        st.metric('Total Revenue', formatted_revenue)


# Fungsi untuk menampilkan visualisasi status pesanan
def create_order_status_viz(df):
    st.subheader('Jumlah Pesanan berdasarkan Status')
    order_count = df['order_status'].value_counts()
    fig, ax = plt.subplots(figsize=(10, 6))
    order_count.plot(kind='bar', ax=ax)
    plt.title('Jumlah Pesanan berdasarkan Status')
    plt.xlabel('Status Pesanan')
    plt.ylabel('Jumlah Pesanan')
    st.pyplot(fig)


# Main function
def main():
    st.title('Analisis Data Pesanan')

    # Load_data
    all_df = load_data()

    # sidebar_filterValues
    start_date, end_date, select_status = create_sidebar(all_df)

    # Filter_data
    main_df = filter_data(all_df, start_date, end_date, select_status)

    # Visualization
    st.subheader(f'Visualisasi Data untuk Status: {select_status}')

    create_order_stats(main_df)

    create_best_worst_category(main_df)
    plot_time_based_orders(main_df, 'M', 'Monthly Sales Graph')
    plot_time_based_orders(main_df, 'D', 'Daily Sales Graph')
    rfm_analysis(main_df)
    create_order_status_viz(main_df)
    geoanalyze(main_df)
    clustering(main_df)

    st.subheader('Order Data')
    st.dataframe(main_df)


if __name__ == "__main__":
    main()
