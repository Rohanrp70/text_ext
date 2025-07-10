provider "aws" {
  region  = "ap-south-1"
  profile = "terraform-rohan"
}

# -------------------------------
# S3 Bucket to Upload Documents
# -------------------------------
resource "aws_s3_bucket" "doc_upload" {
  bucket = "doc-upload-bucket-proj-1"
}

# -----------------------------------------------
# DynamoDB Table to Store Extracted Metadata
# -----------------------------------------------
resource "aws_dynamodb_table" "doc_metadata" {
  name         = "DocumentMetadata"
  hash_key     = "doc_id"
  billing_mode = "PAY_PER_REQUEST"

  attribute {
    name = "doc_id"
    type = "S"
  }
}

# ------------------------------
# IAM Role for Lambda Execution
# ------------------------------
resource "aws_iam_role" "lambda_exec" {
  name = "lambda_exec_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect = "Allow",
      Principal = {
        Service = "lambda.amazonaws.com"
      },
      Action = "sts:AssumeRole"
    }]
  })
}

# --------------------------------------------------
# IAM Policy for Lambda to access AWS services
# --------------------------------------------------
resource "aws_iam_policy" "lambda_permissions" {
  name = "lambda_s3_textract_dynamodb_access"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "s3:GetObject"
        ],
        Resource = [
          "arn:aws:s3:::${aws_s3_bucket.doc_upload.bucket}/*"
        ]
      },
      {
        Effect = "Allow",
        Action = [
          "textract:AnalyzeDocument",
          "textract:StartDocumentAnalysis",
          "textract:GetDocumentAnalysis"
        ],
        Resource = "*"
      },
      {
        Effect = "Allow",
        Action = [
          "dynamodb:PutItem"
        ],
        Resource = aws_dynamodb_table.doc_metadata.arn
      },
      {
        Effect = "Allow",
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "attach_lambda_permissions" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = aws_iam_policy.lambda_permissions.arn
}

# ------------------------
# Lambda Function
# ------------------------
resource "aws_lambda_function" "process_document" {
  function_name = "process_document_lambda"
  role          = aws_iam_role.lambda_exec.arn
  runtime       = "python3.9"
  handler       = "handler.lambda_handler"

  filename         = "backend/lambda/function.zip"
  source_code_hash = filebase64sha256("backend/lambda/function.zip")
  timeout = 30
  environment {
    variables = {
      TABLE_NAME      = aws_dynamodb_table.doc_metadata.name
      OPENAI_API_KEY  = var.openai_api_key
    }
  }

  depends_on = [aws_iam_role_policy_attachment.attach_lambda_permissions]
}

# ---------------------------------
# Allow S3 to Invoke Lambda
# ---------------------------------
resource "aws_lambda_permission" "allow_s3_invoke" {
  statement_id  = "AllowS3Invoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.process_document.arn
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.doc_upload.arn
}

# -----------------------------------
# Trigger Lambda on S3 Upload
# -----------------------------------
resource "aws_s3_bucket_notification" "trigger_lambda" {
  bucket = aws_s3_bucket.doc_upload.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.process_document.arn
    events              = ["s3:ObjectCreated:*"]
  }

  depends_on = [aws_lambda_permission.allow_s3_invoke]
}
