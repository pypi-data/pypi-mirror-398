import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Union

class FunctionOutputManager:
    def __init__(self, csv_file: Optional[Union[str, Path]] = None):
        default_csv = Path(__file__).resolve().parent / "output_info.csv"
        self.csv_file = csv_file if csv_file else default_csv
        self.df = self.load_or_create_csv()
    
    def load_or_create_csv(self) -> pd.DataFrame:
        """Load existing CSV or create new one with proper structure"""
        if isinstance(self.csv_file, str) and self.csv_file.startswith(("http://", "https://")):
            return pd.read_csv(self.csv_file)

        csv_path = Path(self.csv_file)
        if csv_path.exists():
            return pd.read_csv(csv_path)
        raise FileNotFoundError(f"output card not found at {csv_path}")
    
    def get_extension(self, scenario_flag: str,algorithm: str,output_var: str, **user_inputs) -> str:
        matches = self.df[(self.df['scenario_flag'] == scenario_flag)
                & (self.df['algorithm'] == algorithm)
                & (self.df['output_var'] == output_var)]

        if len(matches) == 0:
            # Find which specific combinations exist for the given scenario_flag
            scenario_combinations = self.df[self.df['scenario_flag'] == scenario_flag][['algorithm', 'output_var']].drop_duplicates()
            
            error_msg = f"No record found for combination: scenario_flag={scenario_flag}, algorithm={algorithm}, output_var={output_var}\n"
            error_msg += f"Available combinations for scenario_flag {scenario_flag}:\n"
            error_msg += scenario_combinations.to_string(index=False)
            
            raise ValueError(error_msg)

        row = matches.iloc[0]
        return({
            'extension':row['file_extension'],
            'output_dir':row['output_directory']
            })

    def generate_filename(self, scenario_flag: str,algorithm: str,output_var: str, **user_inputs) -> str:
        """Generate filename based on pattern and user inputs"""
        # if scenario_flag not in self.df['scenario_flag'].values:
        #     raise ValueError(f"Scenario '{scenario_flag}' not found in registry")
        # else:
        #     if [(scenario_flag in self.df['scenario_flag'].values) 
        #         & (algorithm not in self.df['algorithm'].values)]:
        #         raise ValueError(f"Algorithm '{algorithm}' not found in registry")
        #     else:
        #         if [(scenario_flag not in self.df['scenario_flag'].values) 
        #         & (algorithm not in self.df['algorithm'].values) 
        #         & (output_var not in self.df['output_var'].values)]:
        #             raise ValueError(f"Output variable '{output_var}' not found in registry")
        
        # row = self.df[(self.df['scenario_flag'] == scenario_flag) 
        #               & (self.df['algorithm'] == algorithm)
        #               & (self.df['output_var'] == output_var)].iloc[0]
        matches = self.df[(self.df['scenario_flag'] == scenario_flag)
                & (self.df['algorithm'] == algorithm)
                & (self.df['output_var'] == output_var)]

        if len(matches) == 0:
            # Find which specific combinations exist for the given scenario_flag
            scenario_combinations = self.df[self.df['scenario_flag'] == scenario_flag][['algorithm', 'output_var']].drop_duplicates()
            
            error_msg = f"No record found for combination: scenario_flag={scenario_flag}, algorithm={algorithm}, output_var={output_var}\n"
            error_msg += f"Available combinations for scenario_flag {scenario_flag}:\n"
            error_msg += scenario_combinations.to_string(index=False)
            
            raise ValueError(error_msg)

        row = matches.iloc[0]

        pattern = row['file_pattern']
        
        
        # Check if this is a download-only file with wildcard pattern
        if row['download_only'] and '*' in pattern:
            # For download-only files with wildcards, return the pattern info
            return {
                'file': pattern,
                'output_dir':row['output_directory'],
                'extension': row['file_extension'],
                'download_only': True,
                'message': f"Files matching pattern '{pattern}' in {row['output_directory']}"
            }
        
        # Replace placeholders in pattern with actual values
        # pattern = urllib.parse.unquote(pattern)

        filename = pattern
        for key, value in user_inputs.items():
            placeholder = f"{{{key}}}"
            filename = filename.replace(placeholder, str(value))
        
        # Add directory path
        return {
            'download_only': False,
            'file': filename,
            'output_dir':row['output_directory'],
            'extension': row['file_extension']
            }
    
    
if __name__ == "__main__":
    # Initialize the manager
    # from output_manager import FunctionOutputManager
    manager = FunctionOutputManager()
    
    # Generate a filename for func1
    filename = manager.generate_filename("snow", "qms","tb",fGHz=16.7, inc_angle=40)
    print(f"Generated filename: {filename}")
        
