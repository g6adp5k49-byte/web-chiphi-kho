import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Cấu hình giao diện Web
st.set_page_config(page_title="Hệ Thống Tính Chi Phí Kho", layout="wide", page_icon="📦")
st.title("📦 HỆ THỐNG TỰ ĐỘNG TÍNH TOÁN CHI PHÍ KHO")
st.markdown("---")

# 2. Hàm hỗ trợ tìm đúng tên cột
def find_column_name(df, keyword):
    for col in df.columns:
        if keyword.lower() in str(col).lower().replace('\n', ' ').strip():
            return col
    return None

# 3. Sidebar - Input dữ liệu
st.sidebar.header("📥 1. Dữ liệu đầu vào")
file_booking = st.sidebar.file_uploader("Tải lên file Booking (Excel/CSV)", type=['csv', 'xlsx'])

if file_booking is not None:
    try:
        # Đọc dữ liệu
        if file_booking.name.endswith('csv'):
            df_booking = pd.read_csv(file_booking)
        else:
            df_booking = pd.read_excel(file_booking)
            
        # Tìm các cột quan trọng
        col_bien_so = find_column_name(df_booking, 'biển số')
        col_tong_kien = find_column_name(df_booking, 'tổng số kiện')
        col_kho_nhan = find_column_name(df_booking, 'kho nhận')
        col_ngay_giao = find_column_name(df_booking, 'ngày giao')

        if not col_tong_kien or not col_kho_nhan:
            st.error("Lỗi: Không tìm thấy cột 'Tổng số kiện' hoặc 'Kho nhận' trong file.")
            st.stop()
            
        # Xử lý Ngày tháng để lấy Tháng/Năm
        if col_ngay_giao:
            df_booking[col_ngay_giao] = pd.to_datetime(df_booking[col_ngay_giao], format='mixed', errors='coerce')
            df_booking['Tháng_Năm'] = df_booking[col_ngay_giao].dt.strftime('%m/%Y').fillna("Khác")
            danh_sach_thang = df_booking['Tháng_Năm'].unique().tolist()
        else:
            df_booking['Tháng_Năm'] = "Mặc định"
            danh_sach_thang = ["Mặc định"]

        # Chọn tháng phân tích
        st.sidebar.markdown("---")
        st.sidebar.header("📅 2. Tùy chỉnh Phân tích")
        thang_chon = st.sidebar.selectbox("Chọn tháng báo cáo:", danh_sach_thang)
        tong_cuoc_van_tai = st.sidebar.number_input(f"Phí vận tải {thang_chon} (VNĐ):", value=152131755, step=1000000)
        
        # Nhập dữ liệu tháng trước để làm Base so sánh
        st.sidebar.markdown("---")
        st.sidebar.header("🔄 3. Base So sánh (Tháng trước)")
        st.sidebar.info("Nhập số liệu tháng trước để hệ thống tìm ra nguyên nhân Tăng/Giảm.")
        tong_cuoc_thang_truoc = st.sidebar.number_input("Tổng cước vận tải tháng trước:", value=126423087, step=1000000)
        tong_kien_thang_truoc = st.sidebar.number_input("Tổng số kiện giao tháng trước:", value=14158, step=1000)

        # LỌC DỮ LIỆU THEO THÁNG
        df_current = df_booking[df_booking['Tháng_Năm'] == thang_chon].copy()
        df_current[col_tong_kien] = pd.to_numeric(df_current[col_tong_kien], errors='coerce').fillna(0)
        df_current[col_kho_nhan] = df_current[col_kho_nhan].astype(str).str.strip()

        # 4. ENGINE TÍNH TOÁN
        tong_so_chuyen = df_current[col_bien_so].nunique() if col_bien_so else 0
        tong_so_kien = df_current[col_tong_kien].sum()
        
        cp_thung_nay = tong_cuoc_van_tai / tong_so_kien if tong_so_kien > 0 else 0
        cp_thung_truoc = tong_cuoc_thang_truoc / tong_kien_thang_truoc if tong_kien_thang_truoc > 0 else 0
        
        # Tính Chênh lệch (Delta)
        delta_kien = tong_so_kien - tong_kien_thang_truoc
        delta_cuoc = tong_cuoc_van_tai - tong_cuoc_thang_truoc
        delta_cp_thung = cp_thung_nay - cp_thung_truoc
        
        pct_kien = (delta_kien / tong_kien_thang_truoc * 100) if tong_kien_thang_truoc else 0
        pct_cuoc = (delta_cuoc / tong_cuoc_thang_truoc * 100) if tong_cuoc_thang_truoc else 0

        # Groupby Kho
        df_kho = df_current.groupby(col_kho_nhan)[col_tong_kien].sum().reset_index()
        df_kho = df_kho[df_kho[col_tong_kien] > 0]
        df_kho = df_kho.rename(columns={col_kho_nhan: 'Kho Nhận Hàng', col_tong_kien: 'Tổng Kiện'})
        
        df_kho['Tỷ trọng (%)'] = (df_kho['Tổng Kiện'] / tong_so_kien) * 100
        df_kho['Phân bổ cước (VNĐ)'] = (df_kho['Tỷ trọng (%)'] / 100) * tong_cuoc_van_tai
        df_kho['Chi phí / Thùng (VNĐ)'] = df_kho['Phân bổ cước (VNĐ)'] / df_kho['Tổng Kiện']
        df_kho = df_kho.sort_values('Chi phí / Thùng (VNĐ)', ascending=False)

        # 5. HIỂN THỊ METRICS
        st.subheader(f"📊 1. Chỉ số Tổng Quan ({thang_chon})")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Tổng Số Chuyến Xe", f"{tong_so_chuyen:,.0f} chuyến")
        
        # Hàng hóa tăng là màu Xanh (Bình thường)
        col2.metric("Tổng Số Thùng Giao", f"{tong_so_kien:,.0f}", f"{delta_kien:,.0f} thùng ({pct_kien:.1f}%)")
        
        # Chi phí tăng là Xấu -> Dùng delta_color="inverse" để đổi màu Đỏ
        col3.metric("Tổng Phí Vận Tải", f"{tong_cuoc_van_tai:,.0f} ₫", f"{delta_cuoc:,.0f} ₫ ({pct_cuoc:.1f}%)", delta_color="inverse")
        col4.metric("Bình quân / Thùng", f"{cp_thung_nay:,.0f} ₫", f"{delta_cp_thung:,.0f} ₫", delta_color="inverse")

        # 6. PHÂN TÍCH NGUYÊN NHÂN TỰ ĐỘNG
        st.markdown("---")
        st.subheader("🤖 2. Phân Tích Nguyên Nhân Biến Động (Auto-Insights)")
        
        if delta_cp_thung > 0:
            loi_nhan = f"⚠️ **CẢNH BÁO:** Chi phí trên từng thùng **TĂNG {delta_cp_thung:,.0f} ₫** so với tháng trước. \n\n**Nguyên nhân gốc rễ (Root Cause):** "
            if delta_cuoc > 0 and delta_kien < 0:
                loi_nhan += f"Tổng cước vận tải bị đội lên **{pct_cuoc:.1f}%** trong khi sản lượng xuất kho lại sụt giảm **{abs(pct_kien):.1f}%**. Việc hàng hóa ít đi nhưng chi phí xe lại tăng chứng tỏ các chuyến xe đang chạy **không đủ tải (Low Fill Rate)**. Cần rà soát lại khâu điều phối và ghép chuyến."
            elif delta_cuoc > 0 and delta_kien > 0:
                loi_nhan += f"Sản lượng xuất kho có tăng (**{pct_kien:.1f}%**), nhưng tổng cước vận tải lại tăng nhanh hơn rất nhiều (**{pct_cuoc:.1f}%**). Mức tăng này không tỷ lệ thuận với lượng hàng. Cần kiểm tra lại có phát sinh phụ phí nhà xe hoặc tuyến đường giao hàng bị thay đổi hay không."
            elif delta_cuoc < 0 and delta_kien < 0:
                loi_nhan += f"Dù bộ phận kho đã nỗ lực giảm tổng cước vận tải (**giảm {abs(pct_cuoc):.1f}%**), tuy nhiên sản lượng hàng hóa lại giảm quá sâu (**giảm {abs(pct_kien):.1f}%**), khiến định phí chia đều cho mỗi thùng bị vọt lên."
            st.error(loi_nhan)
            
        elif delta_cp_thung < 0:
            loi_nhan = f"✅ **TÍCH CỰC:** Chi phí trên từng thùng **GIẢM {abs(delta_cp_thung):,.0f} ₫** so với tháng trước. \n\n**Đánh giá hiệu suất:** "
            if delta_cuoc < 0 and delta_kien > 0:
                loi_nhan += f"Quá tuyệt vời! Cước vận tải giảm (**{abs(pct_cuoc):.1f}%**) trong khi sản lượng xuất kho lại tăng (**{pct_kien:.1f}%**). Bộ phận kho đã tối ưu cực tốt việc ghép chuyến và sử dụng full tải trọng xe."
            elif delta_cuoc > 0 and delta_kien > 0:
                loi_nhan += f"Dù tổng cước vận tải phải tăng (**{pct_cuoc:.1f}%**) do lượng hàng nhiều lên, nhưng sản lượng xuất kho đã tăng rất mạnh (**{pct_kien:.1f}%**), giúp hiệu suất chi phí gánh trên mỗi thùng rẻ đi. Quy mô (Scale) đang phát huy tác dụng tốt!"
            st.success(loi_nhan)
            
        else:
            st.info("Chi phí bình quân trên từng thùng không thay đổi, hoạt động điều phối vận tải đang diễn ra cực kỳ ổn định.")

        st.markdown("---")
        st.subheader("🏭 3. Phân Bổ Chi Phí Từng Kho")
        c1, c2 = st.columns([1, 1])
        with c1:
            fig = px.bar(df_kho, x='Kho Nhận Hàng', y='Chi phí / Thùng (VNĐ)',
                         title="Biểu đồ: Chi Phí Theo Kho Nhận", text_auto='.0f', color='Kho Nhận Hàng')
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
            
        with c2:
            st.markdown("**Bảng ma trận (Chi tiết K0, K1, K2...)**")
            st.dataframe(df_kho.style.format({
                    'Tổng Kiện': '{:,.0f}', 'Tỷ trọng (%)': '{:.2f}%', 
                    'Phân bổ cước (VNĐ)': '{:,.0f} ₫', 'Chi phí / Thùng (VNĐ)': '{:,.0f} ₫'
                }), use_container_width=True)

    except Exception as e:
        st.error(f"Đã xảy ra lỗi khi xử lý dữ liệu: {e}")
else:
    st.info("👈 Vui lòng tải file Booking của bạn lên từ thanh công cụ bên trái để hệ thống bắt đầu tính toán.")
