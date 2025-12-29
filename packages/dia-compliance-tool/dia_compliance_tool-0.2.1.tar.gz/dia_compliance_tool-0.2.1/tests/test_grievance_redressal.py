from Digital_India_Act.LLM_based_Features import GrievanceExtractor
from Digital_India_Act.LLM_based_Features import GrievanceRedressalChecker

extractor = GrievanceExtractor("https://uidai.gov.in/en/")
pages = extractor.extract()

checker = GrievanceRedressalChecker(pages)
result = checker.run()

print(result)