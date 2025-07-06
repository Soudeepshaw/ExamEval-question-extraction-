import asyncio
import aiohttp
import json
import time
from pathlib import Path

class EnhancedAPITester:
    def __init__(self, base_url: str = "http://localhost:8000/api/v1"):
        self.base_url = base_url
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_health_check(self):
        """Test health check endpoint"""
        print("🏥 Testing health check...")
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                data = await response.json()
                if data.get("success"):
                    print("✅ Health check passed")
                    print(f"   Status: {data.get('status')}")
                    print(f"   Response time: {data.get('response_time', 0):.3f}s")
                    return True
                else:
                    print("❌ Health check failed")
                    print(f"   Error: {data.get('error')}")
                    return False
        except Exception as e:
            print(f"❌ Health check error: {str(e)}")
            return False
    
    async def test_capabilities(self):
        """Test capabilities endpoint"""
        print("\n🔧 Testing capabilities...")
        try:
            async with self.session.get(f"{self.base_url}/capabilities") as response:
                data = await response.json()
                if data.get("success"):
                    print("✅ Capabilities retrieved successfully")
                    capabilities = data.get("capabilities", {})
                    print(f"   Model: {capabilities.get('gemini_model')}")
                    print(f"   Max file size: {capabilities.get('max_file_size_mb')}MB")
                    print(f"   Enhanced extraction: {capabilities.get('features', {}).get('content_extraction')}")
                    print(f"   Question types: {capabilities.get('question_types_supported')}")
                    return True
                else:
                    print("❌ Failed to get capabilities")
                    return False
        except Exception as e:
            print(f"❌ Capabilities error: {str(e)}")
            return False
    
    async def test_question_types(self):
        """Test question types endpoint"""
        print("\n📝 Testing question types...")
        try:
            async with self.session.get(f"{self.base_url}/question-types") as response:
                data = await response.json()
                if data.get("success"):
                    print("✅ Question types retrieved successfully")
                    print(f"   Total types: {data.get('total_types')}")
                    
                    # Show first few question types
                    question_types = data.get('data', {}).get('question_types', [])
                    if question_types:
                        print("   Sample types:")
                        for qt in question_types[:5]:
                            print(f"     - {qt.get('type')}: {qt.get('description', 'No description')}")
                    return True
                else:
                    print("❌ Failed to get question types")
                    return False
        except Exception as e:
            print(f"❌ Question types error: {str(e)}")
            return False
    
    async def test_basic_upload(self, pdf_path: str):
        """Test basic upload endpoint"""
        print(f"\n📤 Testing basic upload with {pdf_path}...")
        try:
            if not Path(pdf_path).exists():
                print(f"❌ File not found: {pdf_path}")
                return False
            
            start_time = time.time()
            
            with open(pdf_path, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('file', f, filename=Path(pdf_path).name, content_type='application/pdf')
                
                async with self.session.post(f"{self.base_url}/upload", data=data) as response:
                    result = await response.json()
            
            upload_time = time.time() - start_time
            
            if result.get("success"):
                print("✅ Basic upload successful")
                print(f"   Processing time: {result.get('processing_time', 0):.2f}s")
                print(f"   Total upload time: {upload_time:.2f}s")
                
                # Show structure summary
                data = result.get('data', {})
                summary = data.get('summary', {})
                print(f"   Sections: {summary.get('total_sections', 0)}")
                print(f"   Questions: {summary.get('total_questions', 0)}")
                print(f"   Optional structures: {len(summary.get('optional_structures', []))}")
                
                return True
            else:
                print("❌ Basic upload failed")
                print(f"   Error: {result.get('error')}")
                return False
                
        except Exception as e:
            print(f"❌ Basic upload error: {str(e)}")
            return False
    
    async def test_enhanced_upload(self, pdf_path: str):
        """Test enhanced upload endpoint"""
        print(f"\n🚀 Testing enhanced upload with {pdf_path}...")
        try:
            if not Path(pdf_path).exists():
                print(f"❌ File not found: {pdf_path}")
                return False
            
            start_time = time.time()
            
            with open(pdf_path, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('file', f, filename=Path(pdf_path).name, content_type='application/pdf')
                
                async with self.session.post(f"{self.base_url}/upload-enhanced", data=data) as response:
                    result = await response.json()
            
            upload_time = time.time() - start_time
            
            if result.get("success"):
                print("✅ Enhanced upload successful")
                print(f"   Total processing time: {result.get('processing_time', 0):.2f}s")
                print(f"   Structure extraction: {result.get('structure_extraction_time', 0):.2f}s")
                print(f"   Content extraction: {result.get('content_extraction_time', 0):.2f}s")
                print(f"   Total upload time: {upload_time:.2f}s")
                
                # Show enhanced summary
                data = result.get('data', {})
                summary = data.get('summary', {})
                print(f"   Sections: {summary.get('total_sections', 0)}")
                print(f"   Questions: {summary.get('total_questions', 0)}")
                print(f"   Subquestions: {summary.get('total_subquestions', 0)}")
                
                # Show content extraction details
                sections = data.get('sections', [])
                total_content_items = 0
                total_images = 0
                total_formulas = 0
                
                for section in sections:
                    for question in section.get('questions', []):
                        content = question.get('content', {})
                        if content.get('text'):
                            total_content_items += 1
                        if content.get('images'):
                            total_images += len(content.get('images', []))
                        if content.get('formulas'):
                            total_formulas += len(content.get('formulas', []))
                        
                        # Check subquestions
                        for subq in question.get('subquestions', []):
                            subcontent = subq.get('content', {})
                            if subcontent.get('text'):
                                total_content_items += 1
                            if subcontent.get('images'):
                                total_images += len(subcontent.get('images', []))
                            if subcontent.get('formulas'):
                                total_formulas += len(subcontent.get('formulas', []))
                
                print(f"   Content items extracted: {total_content_items}")
                print(f"   Images described: {total_images}")
                print(f"   Formulas extracted: {total_formulas}")
                
                return True
            else:
                print("❌ Enhanced upload failed")
                print(f"   Error: {result.get('error')}")
                return False
                
        except Exception as e:
            print(f"❌ Enhanced upload error: {str(e)}")
            return False
    
    async def test_content_validation(self, pdf_path: str):
        """Test content validation by comparing basic vs enhanced"""
        print(f"\n🔍 Testing content validation with {pdf_path}...")
        try:
            # Test basic upload with content extraction
            print("   Testing basic upload with content extraction...")
            with open(pdf_path, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('file', f, filename=Path(pdf_path).name, content_type='application/pdf')
                
                async with self.session.post(f"{self.base_url}/upload?extract_content=true", data=data) as response:
                    basic_result = await response.json()
            
            # Test enhanced upload
            print("   Testing enhanced upload...")
            with open(pdf_path, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('file', f, filename=Path(pdf_path).name, content_type='application/pdf')
                
                async with self.session.post(f"{self.base_url}/upload-enhanced", data=data) as response:
                    enhanced_result = await response.json()
            
            if basic_result.get("success") and enhanced_result.get("success"):
                print("✅ Both uploads successful")
                
                # Compare structure
                basic_summary = basic_result.get('data', {}).get('summary', {})
                enhanced_summary = enhanced_result.get('data', {}).get('summary', {})
                
                print(f"   Basic - Sections: {basic_summary.get('total_sections', 0)}, Questions: {basic_summary.get('total_questions', 0)}")
                print(f"   Enhanced - Sections: {enhanced_summary.get('total_sections', 0)}, Questions: {enhanced_summary.get('total_questions', 0)}")
                
                # Structure should match
                if (basic_summary.get('total_sections') == enhanced_summary.get('total_sections') and
                    basic_summary.get('total_questions') == enhanced_summary.get('total_questions')):
                    print("✅ Structure consistency validated")
                    return True
                else:
                    print("⚠️  Structure mismatch detected")
                    return False
            else:
                print("❌ One or both uploads failed")
                return False
                
        except Exception as e:
            print(f"❌ Content validation error: {str(e)}")
            return False
    
    async def run_all_tests(self, pdf_path: str = None):
        """Run all tests"""
        print("🧪 Starting Enhanced API Test Suite")
        print("=" * 50)
        
        results = []
        
        # Basic endpoint tests
        results.append(await self.test_health_check())
        results.append(await self.test_capabilities())
        results.append(await self.test_question_types())
        
        # File upload tests (if PDF provided)
        if pdf_path:
            results.append(await self.test_basic_upload(pdf_path))
            results.append(await self.test_enhanced_upload(pdf_path))
            results.append(await self.test_content_validation(pdf_path))
        else:
            print("\n⚠️  No PDF file provided, skipping upload tests")
            print("   To test uploads, provide a PDF file path")
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 Test Results Summary")
        passed = sum(results)
        total = len(results)
        
        print(f"✅ Passed: {passed}/{total}")
        if passed < total:
            print(f"❌ Failed: {total - passed}/{total}")
        
        success_rate = (passed / total) * 100 if total > 0 else 0
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if success_rate == 100:
            print("🎉 All tests passed! API is working correctly.")
        elif success_rate >= 80:
            print("⚠️  Most tests passed, but some issues detected.")
        else:
            print("❌ Multiple test failures detected. Please check the logs.")
        
        return success_rate >= 80

async def main():
    """Main test function"""
    import sys
    
    # Get PDF path from command line arguments
    pdf_path = None
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        if not Path(pdf_path).exists():
            print(f"❌ PDF file not found: {pdf_path}")
            pdf_path = None
    
    # Run tests
    async with EnhancedAPITester() as tester:
        success = await tester.run_all_tests(pdf_path)
        return success

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n❌ Test suite error: {str(e)}")
        exit(1)

