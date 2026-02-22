"""
Data Analysis Tool
Purpose: Enable agent to analyze CSV data
"""

from typing import Dict, List
import pandas as pd
import json
from io import StringIO
from config.logger import app_logger as logger


class DataAnalysisTool:
    """
    Data analysis tool using pandas
    
    WHY: Enables agent to:
         - Read CSV files
         - Perform statistical analysis
         - Generate insights
         - No external API needed (local processing)
    """
    
    def __init__(self):
        """Initialize data analysis tool"""
        logger.info("DataAnalysisTool initialized")
    
    def analyze_csv(self, csv_data: str, analysis_type: str = "summary") -> Dict:
        """
        Analyze CSV data
        
        Args:
            csv_data: CSV data as string
            analysis_type: Type of analysis ('summary', 'describe', 'head')
            
        Returns:
            Dictionary with analysis results
        """
        
        try:
            # Read CSV
            df = pd.read_csv(StringIO(csv_data))
            
            result = {
                "success": True,
                "rows": len(df),
                "columns": len(df.columns),
                "column_names": df.columns.tolist()
            }
            
            # Perform requested analysis
            if analysis_type == "summary":
                result["summary"] = {
                    "shape": df.shape,
                    "dtypes": df.dtypes.astype(str).to_dict(),
                    "null_counts": df.isnull().sum().to_dict()
                }
                
            elif analysis_type == "describe":
                # Statistical description
                desc = df.describe(include='all').to_dict()
                result["statistics"] = desc
                
            elif analysis_type == "head":
                # First few rows
                result["preview"] = df.head(10).to_dict(orient='records')
            
            logger.info(f"Data analysis completed: {analysis_type}")
            return result
            
        except Exception as e:
            logger.error(f"Data analysis failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def calculate_statistics(self, numbers: List[float]) -> Dict:
        """
        Calculate basic statistics for a list of numbers
        
        Args:
            numbers: List of numbers
            
        Returns:
            Dictionary with statistics
        """
        
        try:
            import statistics
            
            result = {
                "success": True,
                "count": len(numbers),
                "mean": statistics.mean(numbers),
                "median": statistics.median(numbers),
                "stdev": statistics.stdev(numbers) if len(numbers) > 1 else 0,
                "min": min(numbers),
                "max": max(numbers)
            }
            
            logger.info("Statistics calculated")
            return result
            
        except Exception as e:
            logger.error(f"Statistics calculation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_tool_definition(self) -> Dict:
        """Get tool definition for Semantic Kernel"""
        return {
            "name": "analyze_data",
            "description": "Analyze CSV data or calculate statistics. Use this for data analysis tasks, generating insights from datasets, or calculating numerical statistics.",
            "parameters": {
                "type": "object",
                "properties": {
                    "csv_data": {
                        "type": "string",
                        "description": "CSV data as a string"
                    },
                    "analysis_type": {
                        "type": "string",
                        "description": "Type of analysis: 'summary', 'describe', or 'head'",
                        "enum": ["summary", "describe", "head"],
                        "default": "summary"
                    }
                },
                "required": ["csv_data"]
            }
        }


# ====================
# USAGE EXAMPLE
# ====================
if __name__ == "__main__":
    print("\n📊 Testing Data Analysis Tool...")
    
    tool = DataAnalysisTool()
    
    # Test CSV analysis
    csv_data = """name,age,salary
John,30,50000
Jane,25,60000
Bob,35,55000
Alice,28,65000"""
    
    print("\nAnalyzing sample CSV data...")
    result = tool.analyze_csv(csv_data, analysis_type="summary")
    
    if result["success"]:
        print(f"✓ Analysis complete")
        print(f"  Rows: {result['rows']}")
        print(f"  Columns: {result['columns']}")
        print(f"  Column names: {result['column_names']}")
    else:
        print(f"✗ Analysis failed: {result['error']}")
    
    # Test statistics
    print("\nCalculating statistics...")
    numbers = [10, 20, 30, 40, 50]
    stats = tool.calculate_statistics(numbers)
    
    if stats["success"]:
        print(f"✓ Statistics calculated")
        print(f"  Mean: {stats['mean']:.2f}")
        print(f"  Median: {stats['median']:.2f}")
        print(f"  Stdev: {stats['stdev']:.2f}")
    else:
        print(f"✗ Statistics failed: {stats['error']}")
