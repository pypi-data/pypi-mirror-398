resource "aws_iam_role" "example" {
  name               = "example-role"
  assume_role_policy = "{}"
}

resource "aws_iam_role_policy" "inline_policy" {
  name   = "bad-inline-policy"
  role   = aws_iam_role.example.id
  policy = "{}"
}
