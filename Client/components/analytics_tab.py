import streamlit as st
import matplotlib.pyplot as plt
from datetime import datetime


class AnalyticsTab:
    """Tab hiển thị analytics"""

    def render(self):
        """Render UI cho Analytics tab"""
        st.header("Analytics Dashboard")

        self._render_topic_interest()
        self._render_monthly_users()
        self._render_additional_stats()
        self._render_date_filter()

    def _render_topic_interest(self):
        """Biểu đồ topic interest"""
        st.subheader("User Interest by Topic")

        topics = ["Hạnh phúc", "Tư vấn nghề nghiệp", "Sức khỏe", "Mối quan hệ", "Tài chính", "Giáo dục", "Giải trí"]
        values = [65, 48, 38, 55, 30, 42, 25]

        chart_col, metrics_col = st.columns([3, 1])

        with chart_col:
            try:
                fig, ax = plt.subplots(figsize=(10, 6))
                bars = ax.barh(topics, values, color='skyblue')

                for bar in bars:
                    width = bar.get_width()
                    ax.text(width + 1, bar.get_y() + bar.get_height()/2, f'{width}',
                            ha='left', va='center')

                ax.set_title('User Interest by Topic')
                ax.set_xlabel('Number of Chat Sessions')
                st.pyplot(fig)
            except Exception as e:
                st.error(f"Could not render chart: {e}")
                for topic, value in zip(topics, values):
                    st.text(f"{topic}: {'█' * (value // 5)} ({value})")

        with metrics_col:
            st.metric("Total Users", "124", "+12%")
            st.metric("Total Sessions", "312", "+8%")
            st.metric("Avg. Session Time", "8.5 min", "-2%")

    def _render_monthly_users(self):
        """Biểu đồ monthly active users"""
        st.subheader("Monthly Active Users")

        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct"]
        users = [10, 15, 22, 25, 28, 35, 42, 55, 68, 78]

        try:
            fig2, ax2 = plt.subplots(figsize=(10, 4))
            ax2.plot(months, users, marker='o', linestyle='-', color='green')

            for i, v in enumerate(users):
                ax2.text(i, v + 1, str(v), ha='center')

            ax2.set_title('Monthly Active Users')
            ax2.set_xlabel('Month')
            ax2.set_ylabel('Number of Users')
            ax2.grid(True, linestyle='--', alpha=0.7)
            st.pyplot(fig2)
        except Exception as e:
            st.error(f"Could not render chart: {e}")
            for month, value in zip(months, users):
                st.text(f"{month}: {'█' * (value // 5)} ({value})")

    def _render_additional_stats(self):
        """Các stats bổ sung"""
        stats_col1, stats_col2, stats_col3 = st.columns(3)

        with stats_col1:
            st.metric("Top Topic", "Hạnh phúc", "65 chats")

        with stats_col2:
            st.metric("Most Active Day", "Thursday", "+15%")

        with stats_col3:
            st.metric("User Retention", "72%", "+4%")

    def _render_date_filter(self):
        """Filter theo ngày"""
        st.subheader("Filter Data")

        date_col1, date_col2 = st.columns(2)
        with date_col1:
            start_date = st.date_input("Start Date", datetime.now().replace(month=1, day=1))
        with date_col2:
            end_date = st.date_input("End Date", datetime.now())

        if st.button("Update Analytics", key="update_analytics_btn"):
            st.success("Analytics updated!")
            st.info("Note: This is a mock dashboard with sample data.")
