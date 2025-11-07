import streamlit as st
import pandas as pd
import sqlalchemy
from sqlalchemy import create_engine, text
import requests
import json
import re
import hashlib
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

# Page configuration
st.set_page_config(
    page_title="Enterprise NL2SQL with Gemini",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .security-notice {
        background-color: #e8f5e8;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #4caf50;
        margin: 1rem 0;
    }
    .confidential-notice {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ffc107;
        margin: 1rem 0;
    }
    .query-result {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #dee2e6;
        margin: 1rem 0;
    }
    .schema-box {
        background-color: #e3f2fd;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #2196f3;
        margin: 0.5rem 0;
    }
    .table-card {
        background-color: white;
        padding: 0.5rem;
        border-radius: 0.5rem;
        border: 1px solid #ddd;
        margin: 0.25rem 0;
        cursor: pointer;
    }
    .table-card:hover {
        background-color: #f8f9fa;
    }
    .insight-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

def fix_dataframe_types(df):
    """Fix DataFrame types to be compatible with Streamlit"""
    if df is None or not isinstance(df, pd.DataFrame):
        return df
    
    df_fixed = df.copy()
    
    for col in df_fixed.columns:
        if str(df_fixed[col].dtype) == 'Int64':
            df_fixed[col] = df_fixed[col].astype('int64')
        elif str(df_fixed[col].dtype) == 'string':
            df_fixed[col] = df_fixed[col].astype('str')
        elif df_fixed[col].dtype == 'object':
            try:
                pd.to_numeric(df_fixed[col])
            except (ValueError, TypeError):
                df_fixed[col] = df_fixed[col].astype('str')
    
    return df_fixed

class GeminiNL2SQL:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        self.cache_dir = Path("gemini_cache")
        self.cache_dir.mkdir(exist_ok=True)
    
    def get_cache_key(self, question, schema_info):
        """Generate unique cache key"""
        content = f"{question}_{schema_info}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get_cached_response(self, question, schema_info):
        """Get cached Gemini response"""
        cache_key = self.get_cache_key(question, schema_info)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if cache_file.exists():
            with open(cache_file, 'r') as f:
                data = json.load(f)
                cache_time = datetime.fromisoformat(data['timestamp'])
                if (datetime.now() - cache_time).total_seconds() < 3600:
                    return data['response']
        return None
    
    def cache_response(self, question, schema_info, response):
        """Cache Gemini response"""
        cache_key = self.get_cache_key(question, schema_info)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        cache_data = {
            'question': question,
            'schema_info': schema_info,
            'response': response,
            'timestamp': datetime.now().isoformat()
        }
        
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f)
    
    def generate_sql_with_gemini(self, question, schema_info, confidential_mode=False):
        """Generate SQL using Gemini API"""
        try:
            # Check cache first
            cached_response = self.get_cached_response(question, schema_info)
            if cached_response:
                st.info("📦 Using cached response")
                return self.extract_sql_from_response(cached_response)
            
            # Build the prompt with confidentiality settings
            prompt = self.build_sql_prompt(question, schema_info, confidential_mode)
            
            # Prepare API request
            headers = {
                'Content-Type': 'application/json',
                'X-goog-api-key': self.api_key
            }
            
            data = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.1,
                    "maxOutputTokens": 1000,
                }
            }
            
            # Make API request
            with st.spinner("🤔 Gemini is generating SQL query..."):
                response = requests.post(
                    self.base_url,
                    headers=headers,
                    json=data,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if 'candidates' in result and len(result['candidates']) > 0:
                        sql_response = result['candidates'][0]['content']['parts'][0]['text']
                        
                        # Cache the response
                        self.cache_response(question, schema_info, sql_response)
                        
                        return self.extract_sql_from_response(sql_response)
                    else:
                        st.error("No response from Gemini API")
                        return self.fallback_sql_generation(question, confidential_mode)
                else:
                    st.error(f"Gemini API error: {response.status_code} - {response.text}")
                    return self.fallback_sql_generation(question, confidential_mode)
            
        except Exception as e:
            st.error(f"Gemini query failed: {str(e)}")
            return self.fallback_sql_generation(question, confidential_mode)
    
    def build_sql_prompt(self, question, schema_info, confidential_mode=False):
        """Build optimized prompt for SQL generation"""
        confidentiality_note = ""
        if confidential_mode:
            confidentiality_note = """
CONFIDENTIALITY NOTE: Do NOT include sensitive personal information like:
- Email addresses
- Phone numbers
- Full addresses
- Salary information
- Personal identification numbers
Use aggregated data and general information only.
"""
        
        return f"""
You are an expert SQL query generator for MySQL. Given this database schema and question, generate ONLY a MySQL SELECT query.

DATABASE SCHEMA:
{schema_info}

QUESTION: {question}

{confidentiality_note}

RULES:
- Generate ONLY the SQL query, no explanations
- Use proper JOINs for related tables
- Add WHERE clauses for filtering
- Use ORDER BY when sorting is needed
- Include LIMIT for large tables
- Use aggregate functions (COUNT, SUM, AVG) when appropriate
- Handle dates with CURDATE(), DATE_SUB()
- Use table aliases for readability
- Return only the SQL query, nothing else

TABLE RELATIONSHIPS:
- employees.officeCode → offices.officeCode
- customers.salesRepEmployeeNumber → employees.employeeNumber
- orders.customerNumber → customers.customerNumber
- orderdetails.orderNumber → orders.orderNumber
- orderdetails.productCode → products.productCode
- products.productLine → productlines.productLine

EXAMPLES:
Question: "How many customers from France?"
SQL: SELECT COUNT(*) as customer_count FROM customers WHERE country = 'France'

Question: "Top 5 products by profit margin"
SQL: SELECT productName, (MSRP - buyPrice) as profit_margin FROM products ORDER BY profit_margin DESC LIMIT 5

Now generate the SQL for: {question}
"""
    
    def extract_sql_from_response(self, response):
        """Extract SQL query from Gemini response"""
        # Clean the response
        response = re.sub(r'```sql|```', '', response)
        
        # Find SQL query
        sql_match = re.search(r'(SELECT\s+.*?)(?=;|$)', response, re.IGNORECASE | re.DOTALL)
        if sql_match:
            sql_query = sql_match.group(1).strip()
            if not sql_query.endswith(';'):
                sql_query += ';'
            return sql_query
        
        return response.strip()
    
    def fallback_sql_generation(self, question, confidential_mode=False):
        """Enhanced fallback SQL generation"""
        question_lower = question.lower()
        
        # Confidential mode adjustments
        confidential_select = "customerName, country, creditLimit" if confidential_mode else "*"
        
        rules = [
            (r'how many.*employee', "SELECT COUNT(*) as total_employees FROM employees"),
            (r'count.*customer', "SELECT COUNT(*) as total_customers FROM customers"),
            (r'list.*customer.*(\w+)', f"SELECT {confidential_select} FROM customers WHERE country = '{{}}' LIMIT 50"),
            (r'customer.*from.*(\w+)', f"SELECT {confidential_select} FROM customers WHERE country = '{{}}' LIMIT 50"),
            (r'product.*stock.*less than (\d+)', "SELECT productName, quantityInStock FROM products WHERE quantityInStock < {}"),
            (r'low.*stock', "SELECT productName, quantityInStock FROM products WHERE quantityInStock < 100 ORDER BY quantityInStock"),
            (r'top.*product.*price', "SELECT productName, buyPrice FROM products ORDER BY buyPrice DESC LIMIT 10"),
            (r'customer.*credit.*high', "SELECT customerName, creditLimit FROM customers ORDER BY creditLimit DESC LIMIT 10"),
            (r'order.*status.*(\w+)', "SELECT orderNumber, orderDate, status FROM orders WHERE status = '{}'"),
            (r'employee.*office', "SELECT e.firstName, e.lastName, e.jobTitle, o.city FROM employees e JOIN offices o ON e.officeCode = o.officeCode"),
        ]
        
        for pattern, template in rules:
            match = re.search(pattern, question_lower)
            if match:
                if '{}' in template:
                    groups = match.groups()
                    if groups:
                        country_map = {'france': 'France', 'usa': 'USA', 'french': 'France', 'us': 'USA'}
                        value = country_map.get(groups[0].lower(), groups[0].title())
                        return template.format(value)
                return template
        
        # Default fallbacks with confidential mode
        if any(word in question_lower for word in ['employee', 'staff']):
            select_cols = "employeeNumber, firstName, lastName, jobTitle, officeCode" if confidential_mode else "*"
            return f"SELECT {select_cols} FROM employees LIMIT 20"
        elif any(word in question_lower for word in ['customer', 'client']):
            select_cols = "customerName, country, creditLimit" if confidential_mode else "*"
            return f"SELECT {select_cols} FROM customers LIMIT 20"
        elif any(word in question_lower for word in ['product']):
            return "SELECT productName, productLine, quantityInStock FROM products LIMIT 20"
        elif any(word in question_lower for word in ['order']):
            return "SELECT orderNumber, orderDate, status FROM orders LIMIT 20"
        else:
            return "SELECT COUNT(*) as count FROM employees"

class DatabaseManager:
    def __init__(self):
        self.engine = None
        self.schema_info = ""
        self.tables_info = {}
        
    def connect(self, host, user, password, database, port=3306):
        """Connect to MySQL database"""
        try:
            connection_string = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
            self.engine = create_engine(connection_string)
            
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            self.extract_schema_info()
            return True
        except Exception as e:
            st.error(f"Database connection failed: {str(e)}")
            return False
    
    def extract_schema_info(self):
        """Extract detailed schema information"""
        try:
            schema_parts = []
            
            with self.engine.connect() as conn:
                # Get table information
                tables_result = conn.execute(text("SHOW TABLES"))
                tables = [row[0] for row in tables_result]
                
                for table in tables:
                    # Get column details
                    columns_result = conn.execute(text(f"DESCRIBE {table}"))
                    columns_info = []
                    for col in columns_result:
                        col_info = {
                            'name': col[0],
                            'type': col[1],
                            'key': col[3]
                        }
                        columns_info.append(col_info)
                    
                    self.tables_info[table] = columns_info
                    
                    # Format for schema display
                    col_display = []
                    for col in columns_info:
                        col_str = f"{col['name']} ({col['type']})"
                        if col['key'] == 'PRI':
                            col_str += " 🔑"
                        elif col['key'] == 'MUL':
                            col_str += " 🔗"
                        col_display.append(col_str)
                    
                    schema_parts.append(f"TABLE: {table}\nCOLUMNS: {', '.join(col_display)}")
            
            self.schema_info = "\n\n".join(schema_parts)
            
        except Exception as e:
            st.error(f"Schema extraction failed: {str(e)}")
    
    def execute_query(self, sql_query):
        """Execute SQL query and return results"""
        try:
            if not self.validate_query_security(sql_query):
                return "SECURITY_ERROR: Only SELECT queries are allowed"
            
            with self.engine.connect() as conn:
                result = conn.execute(text(sql_query))
                columns = result.keys()
                data = result.fetchall()
                
                df = pd.DataFrame(data, columns=columns)
                return fix_dataframe_types(df)
        except Exception as e:
            return f"Query execution failed: {str(e)}"
    
    def validate_query_security(self, sql_query):
        """Validate query security"""
        sql_upper = sql_query.upper().strip()
        
        forbidden_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE', 'TRUNCATE']
        for keyword in forbidden_keywords:
            if keyword in sql_upper:
                return False
        
        return sql_upper.startswith('SELECT')
    
    def get_table_stats(self):
        """Get table statistics"""
        try:
            stats = {}
            with self.engine.connect() as conn:
                tables_result = conn.execute(text("SHOW TABLES"))
                tables = [row[0] for row in tables_result]
                
                for table in tables:
                    count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = count_result.fetchone()[0]
                    stats[table] = count
            
            return stats
        except:
            return {}
    
    def get_quick_insights(self):
        """Generate quick insights about the database"""
        insights = []
        try:
            with self.engine.connect() as conn:
                # Total employees
                result = conn.execute(text("SELECT COUNT(*) FROM employees"))
                emp_count = result.fetchone()[0]
                insights.append(f"👥 **{emp_count}** Total Employees")
                
                # Total customers
                result = conn.execute(text("SELECT COUNT(*) FROM customers"))
                cust_count = result.fetchone()[0]
                insights.append(f"👥 **{cust_count}** Total Customers")
                
                # Total products
                result = conn.execute(text("SELECT COUNT(*) FROM products"))
                prod_count = result.fetchone()[0]
                insights.append(f"📦 **{prod_count}** Products in Catalog")
                
                # Total orders
                result = conn.execute(text("SELECT COUNT(*) FROM orders"))
                order_count = result.fetchone()[0]
                insights.append(f"📋 **{order_count}** Total Orders")
                
                # Offices count
                result = conn.execute(text("SELECT COUNT(*) FROM offices"))
                office_count = result.fetchone()[0]
                insights.append(f"🏢 **{office_count}** Office Locations")
                
        except Exception as e:
            insights = ["🔍 Connect to database to see insights"]
        
        return insights

def save_query_history(history):
    """Save query history to file"""
    try:
        with open("query_history.json", "w") as f:
            json.dump(history, f)
    except:
        pass

def load_query_history():
    """Load query history from file"""
    try:
        with open("query_history.json", "r") as f:
            return json.load(f)
    except:
        return []

def main():
    st.markdown('<div class="main-header">🔒 Enterprise NL2SQL with Gemini</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Advanced Analytics • Confidential Data Protection • Query History</div>', unsafe_allow_html=True)
    
    # Initialize session state
    if 'gemini_agent' not in st.session_state:
        st.session_state.gemini_agent = None
    if 'db_manager' not in st.session_state:
        st.session_state.db_manager = DatabaseManager()
    if 'query_history' not in st.session_state:
        st.session_state.query_history = load_query_history()
    if 'confidential_mode' not in st.session_state:
        st.session_state.confidential_mode = False
    if 'selected_table' not in st.session_state:
        st.session_state.selected_table = None
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Confidential Mode Toggle
        st.session_state.confidential_mode = st.checkbox(
            "🔒 Confidential Mode", 
            value=st.session_state.confidential_mode,
            help="Hide sensitive personal information from results"
        )
        
        if st.session_state.confidential_mode:
            st.markdown("""
            <div class="confidential-notice">
                <strong>Confidential Mode Active</strong><br>
                Sensitive data will be filtered from results
            </div>
            """, unsafe_allow_html=True)
        
        # Gemini API Key
        gemini_key = st.text_input("🔑 Gemini API Key", type="password", 
                                 help="Your Gemini API key")
        
        if gemini_key:
            st.session_state.gemini_agent = GeminiNL2SQL(gemini_key)
            st.success("✅ Gemini 2.0 Flash Ready!")
        
        # Database connection
        st.header("🔗 Database Connection")
        host = st.text_input("Host", value="localhost")
        user = st.text_input("Username", value="root")
        password = st.text_input("Password", type="password")
        database = st.text_input("Database", value="company_db")
        port = st.number_input("Port", value=3306)
        
        if st.button("🚀 Connect to Database"):
            with st.spinner("Connecting..."):
                if st.session_state.db_manager.connect(host, user, password, database, port):
                    st.success("✅ Database Connected!")
                else:
                    st.error("❌ Connection Failed")
        
        # Database Schema Explorer
        if st.session_state.db_manager.engine:
            st.header("📊 Database Schema")
            
            # Quick Insights
            st.subheader("📈 Quick Insights")
            insights = st.session_state.db_manager.get_quick_insights()
            for insight in insights:
                st.markdown(f'<div class="insight-card">{insight}</div>', unsafe_allow_html=True)
            
            # Table Explorer
            st.subheader("🗃️ Tables")
            for table_name, columns in st.session_state.db_manager.tables_info.items():
                with st.expander(f"📋 {table_name}"):
                    for col in columns:
                        icon = "🔑" if col['key'] == 'PRI' else "🔗" if col['key'] == 'MUL' else "📝"
                        st.write(f"{icon} `{col['name']}` - {col['type']}")
                    
                    if st.button(f"Query {table_name}", key=f"btn_{table_name}"):
                        st.session_state.question = f"Show sample data from {table_name}"
                        st.rerun()
        
        # Query History
        st.header("📜 Query History")
        if st.session_state.query_history:
            for i, (q, sql, timestamp) in enumerate(st.session_state.query_history[-10:]):
                with st.expander(f"🕒 {timestamp}: {q[:30]}..."):
                    st.code(sql, language="sql")
                    if st.button("🔄 Re-run", key=f"rerun_{i}"):
                        st.session_state.question = q
                        st.rerun()
        
        # Clear History Button
        if st.button("🗑️ Clear History"):
            st.session_state.query_history = []
            save_query_history([])
            st.success("History cleared!")
    
    # Main content
    tab1, tab2, tab3 = st.tabs(["💬 Query Interface", "📊 Advanced Analytics", "🔍 Schema Explorer"])
    
    with tab1:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.header("💬 Natural Language Query")
            
            question = st.text_area(
                "Ask anything about your data:",
                height=100,
                placeholder="e.g., Show me customers from France with high credit limits...",
                key="question_input"
            )
            
            if st.button("🚀 Generate & Execute SQL", type="primary") and question:
                if not st.session_state.gemini_agent:
                    st.error("Please enter Gemini API key")
                    return
                
                if not st.session_state.db_manager.engine:
                    st.error("Please connect to database first")
                    return
                
                # Generate SQL
                sql_query = st.session_state.gemini_agent.generate_sql_with_gemini(
                    question, 
                    st.session_state.db_manager.schema_info,
                    st.session_state.confidential_mode
                )
                
                st.subheader("📋 Generated SQL")
                st.code(sql_query, language="sql")
                
                # Execute query
                with st.spinner("🔄 Executing query..."):
                    result = st.session_state.db_manager.execute_query(sql_query)
                    
                    # Save to history
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                    st.session_state.query_history.append((question, sql_query, timestamp))
                    save_query_history(st.session_state.query_history)
                    
                    if isinstance(result, pd.DataFrame):
                        st.subheader("📊 Results")
                        
                        # Metrics
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Rows", len(result))
                        with col2:
                            st.metric("Columns", len(result.columns))
                        with col3:
                            st.metric("Status", "✅ Success")
                        
                        # Data display
                        st.dataframe(result)
                        
                        # Download
                        csv = result.to_csv(index=False)
                        st.download_button(
                            "📥 Download CSV",
                            csv,
                            "query_results.csv",
                            "text/csv"
                        )
                    else:
                        st.error(f"❌ {result}")
        
        with col2:
            st.header("💡 Quick Actions")
            
            quick_queries = [
                "Count total employees by office",
                "List top 10 customers by credit limit",
                "Products with quantity less than 50",
                "Orders by status this month",
                "Employee distribution by job title",
                "Sales performance by product line",
                "Customer count by country",
                "Average order value",
                "Products never ordered",
                "Monthly sales trend"
            ]
            
            for query in quick_queries:
                if st.button(query, use_container_width=True, key=f"quick_{hash(query)}"):
                    st.session_state.question = query
                    st.rerun()
    
    with tab2:
        st.header("📊 Advanced Business Analytics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📈 Sales Dashboard", use_container_width=True):
                st.session_state.question = "Show monthly sales trend for the last 6 months with product line breakdown"
                st.rerun()
            
            if st.button("👥 Employee Analytics", use_container_width=True):
                st.session_state.question = "Show employee count by office location and job title with percentages"
                st.rerun()
        
        with col2:
            if st.button("💰 Financial Overview", use_container_width=True):
                st.session_state.question = "Show total payments by customer and credit limit utilization"
                st.rerun()
            
            if st.button("📦 Inventory Analysis", use_container_width=True):
                st.session_state.question = "Show products by vendor with stock levels and reorder recommendations"
                st.rerun()
        
        with col3:
            if st.button("🌍 Geographic Analysis", use_container_width=True):
                st.session_state.question = "Show customer distribution by country and average credit limit"
                st.rerun()
            
            if st.button("🚚 Operations Metrics", use_container_width=True):
                st.session_state.question = "Show order fulfillment times and status distribution"
                st.rerun()
    
    with tab3:
        st.header("🔍 Database Schema Explorer")
        
        if st.session_state.db_manager.engine:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📋 Complete Schema")
                st.text_area("Database Schema", 
                           st.session_state.db_manager.schema_info, 
                           height=400,
                           disabled=True)
            
            with col2:
                st.subheader("🔗 Table Relationships")
                st.markdown("""
                **Database Relationships:**
                - 🏢 **offices** ← 🔗 → **employees** (officeCode)
                - 👥 **employees** ← 🔗 → **customers** (salesRepEmployeeNumber)
                - 👤 **customers** ← 🔗 → **orders** (customerNumber)
                - 📋 **orders** ← 🔗 → **orderdetails** (orderNumber)
                - 📦 **products** ← 🔗 → **orderdetails** (productCode)
                - 🏷️ **productlines** ← 🔗 → **products** (productLine)
                - 💰 **customers** ← 🔗 → **payments** (customerNumber)
                """)
                
                st.subheader("📊 Table Statistics")
                stats = st.session_state.db_manager.get_table_stats()
                for table, count in stats.items():
                    st.metric(table, f"{count:,} rows")

if __name__ == "__main__":
    main()