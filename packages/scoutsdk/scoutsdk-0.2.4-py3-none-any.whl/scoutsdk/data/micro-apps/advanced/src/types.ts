export type Step = 'idle' | 'uploading' | 'preparing' | 'starting' | 'done';

export interface MyCustomFunctionRequest {
  input_protected_file_url: string;
  input_original_filename: string;
}

export type MyExampleUserData = {
  step: Step;
  error_logs?: string | null;
  input_filename?: string;
  input_protected_file_path?: string;
  output_protected_file_path?: string;
  output_filename?: string;
};
