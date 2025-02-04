from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = "https://ltwbebdjxlsunezjnfwr.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imx0d2JlYmRqeGxzdW5lempuZndyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzczOTkwODMsImV4cCI6MjA1Mjk3NTA4M30.z0VtpKr0Xip397YQKSR00dd-aCgT75-t2tzI7L5mxFQ"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
