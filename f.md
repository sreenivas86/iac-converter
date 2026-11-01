iac-converter/
├── pyproject.toml
├── README.md
├── src/
│   └── iac_converter/
│       ├── __init__.py
│       │
│       ├── api/
│       │   ├── __init__.py
│       │   └── app.py
│       │
│       ├── compiler/
│       │   ├── __init__.py
│       │   ├── yaml_to_ir.py
│       │   └── terraform_to_ir.py
│       │
│       ├── generator/
│       │   ├── __init__.py
│       │   ├── terraform.py
│       │   └── yaml.py
│       │
│       ├── parser/
│       │   ├── __init__.py
│       │   ├── yaml_parser.py
│       │   └── terraform_parser.py
│       │
│       ├── ir/
│       │   ├── __init__.py
│       │   ├── model.py
│       │   ├── resource.py
│       │   ├── provider.py
│       │   ├── variable.py
│       │   ├── output.py
│       │   ├── data_source.py
│       │   ├── expression.py
│       │   └── reference.py
│       │
│       ├── project/
│       │   ├── __init__.py
│       │   ├── project.py
│       │   └── archive.py
│       │
│       └── schema/
│           ├── __init__.py
│           └── provider_schema.py
│
├── tests/
│   ├── unit/
│   │   └── ir/
│   └── integration/
│
├── examples/
│   └── aws/
│
└── .gitignore
-------------------------------------------------------------------------------------------------

✅ M1 — Single-file conversion
   YAML ↔ IR ↔ Terraform

   

        ↓

✅ M2 — Project conversion
   Directory/ZIP ↔ ProjectIR
        ↓
🔨M2.2- load a real directory into Project.

        ↓

🔨 M3 — Robust Terraform expressions
   Traversals
   var.foo
   data.aws_x.y
   module.foo.bar
   indexing
   functions
   conditionals
   for expressions

        ↓

🔨 M4 — Provider schema integration
   terraform providers schema

        ↓

🔨 M5 — Conversion API
   FastAPI
   POST /convert
   ZIP upload/download

        ↓

🔨 M6 — Project storage
   projects
   source format
   generated format
   metadata

        ↓

🔨 M7 — Terraform execution
   init
   plan
   apply
   destroy
   terraform.tfstate






   --------------------------------

   Terraform files
      ↓
  load_project()
      ↓
    Project
      ↓
parse_terraform_project()
      ↓
   ProjectIR
      ↓
generate_terraform_project()
      ↓
    Project
      ↓
  save_project()
      ↓
Terraform files


--------------------------------------------- 06-10-2026




✅ Basic resources
✅ Providers
✅ Variables
✅ Outputs
✅ Expressions
✅ References
✅ Project directories
✅ ZIP projects
✅ Terraform → YAML round trip
✅ YAML → Terraform round trip
⬇
NEXT
Data sources + locals
⬇
depends_on
⬇
count / for_each
⬇
provider aliases
⬇
lifecycle
⬇
nested blocks
⬇
complex expressions
⬇
dynamic blocks
⬇
Provider schemas
⬇
API
⬇
Terraform validate / plan / apply

-----------next target ----------
So the next milestone would be:

M3 — Advanced Terraform blocks

Provisioner connection
Dynamic blocks
Nested blocks
More expression preservation
Stronger round-trip tests

I'd do connection blocks next, one feature at a time just like we've been doing.

M3.2-- terraform nested blocks
Our current IR handles:

resources
attributes
count
for_each
depends_on
lifecycle
provisioners
provisioner connections
providers
variables
data sources
outputs
locals
expressions
references
But it doesn't yet have a first-class representation for arbitrary nested blocks.
------------------
M1.4 — Expression and reference semantics

Test and preserve:

aws_s3_bucket.example
aws_s3_bucket.example.id
data.aws_ami.example.id
var.bucket_name
local.bucket_prefix
each.value
self.public_ip
file("...")
${var.foo} interpolation
complex expressions such as conditional expressions and indexing
----------------------








----------- tasks ---------------27-10-26
1

Expression round-tripping
Next step
Test nested collections containing references, function calls, and conditional expressions in both conversion directions. Verify that expressions don't accidentally become quoted strings or lose their structure.



2

Tuple and collection semantics

Terraform uses square-bracket syntax for tuple/list constructors, and YAML has no native tuple type. Decide how to preserve or represent tuple-versus-list distinctions, potentially using type information or an explicit serialization convention.



3

Full IR coverage

Audit how resources, data sources, providers, variables, outputs, locals, lifecycle rules, provisioners, dependencies, and metadata are represented and preserved across both formats.



4

Provider and resource coverage

S3 is our initial AWS provider/resource focus. Expand and verify support for additional AWS resources, data sources, and provider-specific attributes as required by the project.



5

Validation and error handling

Improve handling of malformed YAML, unsupported Terraform expressions, invalid collection structures, and conversion errors with useful messages.




6

End-to-end verification

Test complete YAML → IR → Terraform and Terraform → IR → YAML conversions on realistic infrastructure examples, including comparisons of semantic equivalence and, where possible, Terraform validation.



7

Production readiness

Review the CLI/API, documentation, supported-feature matrix, fixtures, packaging, and continuous integration.


------------------------- 


01-11-26 ----------------------------

IaC Converter – Updated Project Roadmap
Core conversion implemented
166 tests passing

Your project has progressed from a single-file YAML/Terraform converter into a project-level, bidirectional conversion tool with ZIP support and a FastAPI interface.

Below is the consolidated roadmap, including completed work, work in progress, and what remains.
1. Overall project roadmap
Milestone	Description	Status
M1	Single-file YAML ↔ Terraform conversion	Complete
M2	Project-level conversion	Complete
M2.2	Directory loading and project handling	Complete
M3	Advanced Terraform language support	Complete
M4	YAML schema validation	Complete
M5	FastAPI and ZIP-to-ZIP conversion	Implemented; hardening pending
M6	Project storage and persistence	Audit pending
M7	Terraform execution and validation	Audit pending
M8	End-to-end testing and documentation	Pending
M9	Deployment and production readiness	Pending


2. Completed milestones
M1 – Single-file conversion
Complete
Implemented:
- YAML to Terraform conversion.
- Terraform to YAML conversion.
- Intermediate Representation (IR).
- YAML parser.
- Terraform parser.
- Terraform generator.
- YAML generator.
- Basic round-trip conversion.
M2 – Project-level conversion
Complete
Implemented:
- Terraform project parsing.
- YAML project parsing.
- Project-level IR.
- Multi-file Terraform generation.
- Canonical YAML project generation.
- Project-level round-trip testing.
M2.2 – Directory handling
Complete
Implemented:
- Recursive project directory loading.
- Nested directory support.
- Relative project file paths.
- UTF-8 file handling.
- Cross-platform path handling.
M3 – Advanced Terraform support
Complete
Implemented and tested:
- Nested blocks.
- Nested collections.
- Lists and maps.
- Typed collections.
- Resource lifecycle rules.
- Meta-arguments.
- Provisioners.
- Connection blocks.
- Data sources.
- Locals.
- Complex expressions.
- Filtered map comprehensions.
M4 – Schema validation
Complete
Implemented:
- Pydantic-based YAML schema models.
- Resource validation.
- Variable validation.
- Output validation.
- Provider validation.
- Data source validation.
- Block validation.
- Unknown-field rejection.
- Empty identifier validation.

3. M5 – API and ZIP conversion
Core implementation complete; hardening pending
What we have completed
FastAPI implementation
- Health endpoint.
- YAML-to-Terraform endpoint.
- Terraform-to-YAML endpoint.
- YAML ZIP-to-Terraform ZIP endpoint.
- Terraform ZIP-to-YAML ZIP endpoint.
ZIP functionality
- ZIP archive loading.
- ZIP archive saving.
- Nested project files.
- Duplicate path protection.
- Path traversal protection.
- Invalid archive handling.
- UTF-8 validation.
- Maximum 1,000 files.
- Maximum 10 MB per file.
- Maximum 100 MB total uncompressed content.
API integration tests
- Health endpoint.
- YAML-to-Terraform.
- Terraform-to-YAML.
- Invalid YAML.
- Invalid Terraform ZIP.
- YAML ZIP-to-Terraform ZIP.
- Terraform ZIP-to-YAML ZIP.
What remains in M5
Task	Status
Request-level upload size enforcement	Pending
ZIP decompression security review	Pending
Duplicate YAML resource/variable conflict handling	Pending
API error-handling test coverage	Pending
Dependency declaration audit	Pending
API documentation	Pending
API performance and concurrency testing	Pending

One important distinction: the current endpoint reads at most 100 MB plus one byte, but multipart parsing may already have received and spooled the upload. We should enforce a request-level limit as well.

4. M6 – Storage and persistence
Audit pending
We already have project storage-related modules:
- project/archive.py
- project/loader.py
- project/writer.py
- project/project.py
Remaining work
1. Audit project directory loading.
2. Audit project directory writing.
3. Verify ZIP persistence.
4. Verify nested directory preservation.
5. Test duplicate file handling.
6. Test invalid paths.
7. Test large project handling.
8. Review storage error handling.
9. Add missing integration tests.
Goal: Reliable project storage and retrieval without losing files or changing directory structures unexpectedly.

5. M7 – Terraform execution and validation
Audit pending
This milestone needs an inspection of your existing code before deciding what is already implemented.
Planned work
1. Audit Terraform execution support.
2. Check Terraform CLI availability.
3. Implement or verify terraform fmt.
4. Implement or verify terraform validate.
5. Implement or verify terraform init.
6. Capture execution output.
7. Handle execution timeouts.
8. Handle Terraform errors.
9. Prevent unsafe execution paths.
10. Add execution tests.
Important: Terraform execution should be an explicit, controlled operation. Uploading a ZIP for conversion must never automatically execute Terraform.

6. M8 – Testing and documentation
Pending
Testing
- Full unit test suite.
- Full integration test suite.
- ZIP conversion round trips.
- Large archive tests.
- Invalid input tests.
- API security tests.
- Performance tests.
- Cross-platform tests.
Documentation
- Project README.
- Installation guide.
- Python environment setup.
- API documentation.
- YAML schema documentation.
- Supported Terraform features.
- Conversion examples.
- ZIP upload instructions.
- Error handling guide.
- Limitations and unsupported features.
Example workflow
Document the complete workflow:
YAML files
    |
    v
Create YAML ZIP
    |
    v
Upload to API
    |
    v
YAML ZIP → Terraform ZIP
    |
    v
Download Terraform ZIP
    |
    v
Review generated Terraform
    |
    v
Run Terraform validation



7. M9 – Deployment and production readiness
Pending
Planned work:
- Docker support.
- Environment configuration.
- Production ASGI server configuration.
- Logging.
- Health monitoring.
- Request limits.
- Authentication, if exposed beyond a trusted environment.
- Rate limiting.
- Error monitoring.
- CI/CD pipeline.
- Automated tests in CI.
- Release versioning.
- Deployment documentation.

8. Current test progress
Latest full test run
All passing

166 / 166


API integration tests

7 passed

Archive unit tests

11 passed

Schema unit tests

22 passed

Full suite duration

1.74 seconds



The latest confirmed full test result is 166 passed. This is a test result, not yet a production-readiness certification.

9. Immediate next steps
I recommend following this exact order:
1. M5.1 – API upload security
   
   Enforce request-level upload limits and review ZIP decompression protections.
2. M5.2 – YAML ZIP conflict handling
   
   Detect duplicate resource names, variables, providers, and outputs across YAML documents.
3. M5.3 – API error handling
   
   Add tests for invalid YAML ZIPs, missing YAML files, wrong extensions, oversized uploads, and invalid Terraform projects.
4. M5.4 – Dependency audit
   
   Verify pyproject.toml and development dependencies so a fresh environment can install and run the tests.
5. M6 – Storage audit
   
   Inspect existing implementation and fill any gaps.
6. M7 – Terraform execution audit
   
   Verify existing capabilities before adding new functionality.
7. M8 and M9
   
   Complete documentation, deployment, and production hardening.
10. Project working rules
We'll continue using the same approach:
- One task at a time.
- Exact Windows PowerShell commands.
- Inspect existing code before modifying it.
- Preserve your current uncommitted changes.
- Run targeted tests after each change.
- Run the complete suite after each milestone.
- Mark milestones complete only after verification.
Our next task is M5.1: request-level upload security.

This is the best next step because your two ZIP conversion endpoints are working, and we should secure their upload handling before expanding the API further.