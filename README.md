Enterprise NL2SQL with Gemini
A powerful Streamlit application that converts natural language questions into SQL queries using Google's Gemini AI. This enterprise-grade tool provides advanced analytics, confidential data protection, and comprehensive database exploration capabilities.


<img width="1919" height="968" alt="Screenshot 2025-11-07 105638" src="https://github.com/user-attachments/assets/ee7bfdfa-9cc9-43b0-95b7-ebdd43193025" />
<img width="1919" height="960" alt="Screenshot 2025-11-07 105649" src="https://github.com/user-attachments/assets/27f61b1c-b495-492c-98a1-f3530a562339" />
<img width="1919" height="922" alt="Screenshot 2025-11-07 110626" src="https://github.com/user-attachments/assets/8e11b1c1-b7c4-49a0-afd1-39d348ac937c" />
<img width="1912" height="909" alt="Screenshot 2025-11-07 110635" src="https://github.com/user-attachments/assets/46ff421e-2469-4f8b-a83e-e4d291ac2768" />
<img width="1919" height="899" alt="Screenshot 2025-11-07 110646" src="https://github.com/user-attachments/assets/d416f5fb-0b2a-4b15-9609-7ca1ce6bd424" />

Features
AI-Powered SQL Generation
Natural Language Processing: Convert plain English questions into precise SQL queries

Gemini 2.0 Flash Integration: Fast and accurate AI model for query generation

Smart Query Optimization: Automatic JOINs, WHERE clauses, and aggregations

Query Caching: Intelligent caching for faster repeated queries

Enterprise Security
Confidential Mode: Toggle to hide sensitive personal information

Read-Only Access: Prevents data modification operations

SQL Injection Protection: Comprehensive security validation

Schema-Only Context: AI only sees table structures, not actual data

Advanced Analytics
Quick Insights Dashboard: Real-time database statistics and metrics

Interactive Schema Explorer: Visual table relationships and column details

Pre-built Analytics: Sales dashboards, employee analytics, financial overviews

Geographic Analysis: Customer distribution and regional insights

Data Management
Query History: Persistent storage of all generated queries

One-Click Re-run: Execute previous queries with a single click

CSV Export: Download query results for further analysis

Multi-Table Support: Handles complex database relationships

Installation
Prerequisites
Python 3.8 or higher

MySQL database (or compatible SQL database)

Google Gemini API key

Step 1: Clone or Download
bash
git clone <repository-url>
cd nl2sql-gemini
Step 2: Install Dependencies
bash
pip install -r requirements.txt
Or install manually:

bash
pip install streamlit pandas sqlalchemy pymysql requests pyarrow python-dotenv
Step 3: Set Up Environment (Optional)
Create a .env file in the project root:

env
GEMINI_API_KEY=your_gemini_api_key_here
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=company_db
DB_PORT=3306
Step 4: Run the Application
bash
streamlit run nl2sql_gemini_enhanced.py
📋 Requirements
Core Dependencies
Package	Version	Purpose
streamlit	≥1.28.0	Web application framework
pandas	≥2.0.0	Data manipulation and analysis
sqlalchemy	≥2.0.0	Database ORM and connection
pymysql	≥1.1.0	MySQL database connector
requests	≥2.31.0	HTTP library for API calls
pyarrow	≥14.0.0	Data serialization
python-dotenv	≥1.0.0	Environment variable management
Database Support
✅ MySQL (Primary - using pymysql)

✅ PostgreSQL (with psycopg2-binary)

✅ SQLite (built-in support)

✅ Oracle (with cx_Oracle)

✅ SQL Server (with pyodbc)

🔧 Configuration
Database Connection
Configure your database connection in the sidebar:

Host: Database server address (default: localhost)

Username: Database user (default: root)

Password: Database password

Database: Database name (default: company_db)

Port: Database port (default: 3306)

Gemini API Setup
Visit Google AI Studio

Create a new API key

Enter the key in the application sidebar

🎯 Usage Examples
Basic Queries
"How many employees are there?"

"Show customers from France"

"List products with low stock"

Advanced Analytics
"Monthly sales trend for the last 6 months"

"Employee distribution by office and job title"

"Customer lifetime value analysis"

"Products frequently ordered together"

Complex Joins
"Show orders with customer details and product information"

"Employees and their office locations with manager hierarchy"

"Sales performance by product line and territory"

🏗 Project Structure
text
nl2sql-gemini/
├── nl2sql_gemini_enhanced.py  # Main application
├── requirements.txt           # Python dependencies
├── .env                      # Environment variables (optional)
├── gemini_cache/             # AI response cache
├── query_history.json        # Query history storage
└── README.md                 # This file
🔍 Features Deep Dive
Confidential Mode
When enabled, the application automatically filters out sensitive information:

Email addresses

Phone numbers

Full addresses

Personal identification numbers

Salary information

Schema Explorer
Interactive table navigation

Primary key (🔑) and foreign key (🔗) indicators

Column data types and constraints

Quick sample data queries

Query History
Persistent storage across sessions

Timestamp tracking

One-click re-execution

Export capabilities

 Deployment
Local Development
bash
streamlit run nl2sql_gemini_enhanced.py

Security Considerations
The application only executes SELECT queries

All user input is validated and sanitized

Database credentials are not stored persistently

Gemini API interactions are encrypted

No sensitive data is exposed to the AI model

🐛 Troubleshooting
Common Issues
Database Connection Failed

Verify database credentials

Check network connectivity

Ensure database server is running

Gemini API Errors

Verify API key validity

Check API quota and limits

Ensure proper internet connectivity

Streamlit Compatibility

Update to latest Streamlit version

Check Python version compatibility

Verify all dependencies are installed

Getting Help
Check the application logs for detailed error messages

Verify all environment variables are set correctly

Ensure database user has appropriate read permissions

Performance Tips
Use query caching for frequently asked questions

Enable confidential mode when working with sensitive data

Use LIMIT clauses for large datasets

Regularly clear cache and history for optimal performance

Contributing
We welcome contributions! Please feel free to submit pull requests, report bugs, or suggest new features.

Development Setup
Fork the repository

Create a feature branch

Make your changes

Submit a pull request

License
This project is licensed under the MIT License - see the LICENSE file for details.

🙏 Acknowledgments
Google Gemini AI for powerful natural language processing

Streamlit for the excellent web application framework

SQLAlchemy for robust database connectivity

Pandas for efficient data manipulation

⭐ If you find this project helpful, please give it a star!

For questions or support, please open an issue in the repository.
