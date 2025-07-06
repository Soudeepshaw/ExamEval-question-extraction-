

#!/usr/bin/env python3
"""
Example usage of the Question Paper Analyzer API
"""

import requests
import json
from pathlib import Path

# API base URL
BASE_URL = "http://localhost:8000/api/v1"

def test_health():
    """Test health endpoint"""
    print("🔍 Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_question_types():
    """Test question types endpoint"""
    print("\n🔍 Testing question types endpoint...")
    response = requests.get(f"{BASE_URL}/question-types")
    if response.status_code == 200:
        data = response.json()
        print(f"Found {len(data['question_types'])} question types")
        print("Sample types:")
        for i, qt in enumerate(data['question_types'][:3]):
            print(f"  {i+1}. {qt['type']}")
    else:
        print(f"Error: {response.status_code}")
    return response.status_code == 200

def test_upload(pdf_path):
    """Test PDF upload and analysis"""
    print(f"\n🔍 Testing PDF upload: {pdf_path}")
    
    if not Path(pdf_path).exists():
        print(f"❌ File not found: {pdf_path}")
        return False
    
    try:
        with open(pdf_path, 'rb') as f:
            files = {'file': (Path(pdf_path).name, f, 'application/pdf')}
            response = requests.post(f"{BASE_URL}/upload", files=files, timeout=120)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                print(f"✅ Analysis successful!")
                print(f"Processing time: {data['processing_time']:.2f}s")
                print(f"Sections: {data['data']['summary']['total_sections']}")
                print(f"Questions: {data['data']['summary']['total_questions']}")
                
                # Pretty print the structure
                print("\n📋 Structure:")
                print(json.dumps(data['data'], indent=2))
                return True
            else:
                print(f"❌ Analysis failed: {data['error']}")
        else:
            print(f"❌ Request failed: {response.text}")
        
    except requests.exceptions.Timeout:
        print("⏰ Request timed out (this is normal for large PDFs)")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return False

def main():
    """Main function to run examples"""
    print("🧪 Question Paper Analyzer - Example Usage\n")
    
    # Test basic endpoints
    health_ok = test_health()
    types_ok = test_question_types()
    
    if not (health_ok and types_ok):
        print("\n❌ Basic tests failed. Make sure the server is running.")
        return
    
    # Test PDF upload if sample file exists
    sample_pdf = "tests/sample_papers/sample_question_paper.pdf"
    if Path(sample_pdf).exists():
        test_upload(sample_pdf)
    else:
        print(f"\n📝 To test PDF upload, place a sample PDF at: {sample_pdf}")
        print("Or provide a path to your PDF file:")
        pdf_path = input("PDF path (or press Enter to skip): ").strip()
        if pdf_path and Path(pdf_path).exists():
            test_upload(pdf_path)

if __name__ == "__main__":
    main()
