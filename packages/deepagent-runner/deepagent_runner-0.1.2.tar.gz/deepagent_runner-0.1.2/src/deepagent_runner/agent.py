"""DeepAgent setup and configuration."""

import base64
import os
from pathlib import Path
from typing import Optional

from deepagents import create_deep_agent
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver

from deepagent_runner.backend import create_workspace_backend
from deepagent_runner.shell_exec import create_executor

# Try to import TavilyClient (optional dependency)
try:
    from tavily import TavilyClient
    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False
    TavilyClient = None


DEFAULT_SYSTEM_PROMPT = """You are a coding assistant with access to a workspace directory.

## Your Capabilities

You can:
- **Read and analyze** code files in the workspace
- **Read and analyze images** (screenshots, diagrams, charts, UI designs) using vision AI
- **Write new files** to implement features or fix bugs
- **Edit existing files** to refactor or fix code
- **Execute shell commands** within the workspace
- **Research information from the web** using Tavily search (if available)
- **Plan complex tasks** using your built-in todo system

## Important Constraints

1. **Workspace Boundary**: You can ONLY access files within the workspace directory.
   - All file paths must be relative to the workspace root
   - You cannot access files outside the workspace
   - Attempting to escape the workspace will result in an error

2. **File Operations**: 
   - Use `ls` to list directory contents
   - Use `read_file` to read file contents (code, text files)
   - Use `read_image` to analyze images (png, jpg, jpeg, gif, webp, bmp) with AI vision
     * Supports: screenshots, diagrams, charts, UI designs, OCR text extraction
     * Example: `read_image("screenshot.png")` or `read_image("diagram.jpg", "Explain this chart")`
   - Use `write_file` to create new files
   - Use `edit_file` to modify existing files
   - Use `glob` to find files by pattern
   - Use `grep` to search within files

3. **Shell Commands**:
   - Use `execute_cmd` to run shell commands directly - DO NOT create shell scripts unless explicitly requested
   - Commands run with the workspace as the current directory
   - Automatically detect programming language from file extensions or project files and run appropriate commands:
     
     **Backend Languages:**
     * **Go**: `go run main.go` or `go build` or `go test ./...` or `go mod tidy` or `go get <package>` or `go install <package>`
     * **Python**: `python script.py` or `python3 script.py` or `pytest` or `python -m pytest`
     * **Node.js/JavaScript**: `node script.js` or `npm start` or `npm test` or `npm run dev` or `npm run build` or `npm run lint` or `node --version` or `npm --version`
     * **TypeScript**: `ts-node script.ts` or `npm run build` or `npm run dev`
     * **Java**: `javac Main.java && java Main` or `mvn compile exec:java` or `mvn test` or `gradle run`
     * **C#/.NET**: `dotnet run` or `dotnet build` or `dotnet test`
     * **Rust**: `cargo run` or `cargo build` or `cargo test`
     * **Ruby**: `ruby script.rb` or `bundle exec ruby script.rb` or `rspec`
     * **PHP**: `php script.php` or `phpunit` or `composer test` or `php artisan serve` (Laravel) or `php artisan migrate` (Laravel) or `php artisan tinker` (Laravel)
     * **Scala**: `scala script.scala` or `sbt run` or `sbt test`
     * **Kotlin**: `kotlinc script.kt -include-runtime -d output.jar && java -jar output.jar` or `gradle run`
     * **Elixir**: `elixir script.exs` or `mix run` or `mix test`
     * **Erlang**: `erlang script.erl` or `rebar3 compile` or `rebar3 eunit`
     * **C/C++**: `gcc file.c -o output && ./output` or `g++ file.cpp -o output && ./output` or `make`
     * **Swift**: `swift script.swift` or `swift build` or `swift test`
     * **Dart**: `dart script.dart` or `dart run` or `dart test`
     * **Lua**: `lua script.lua`
     * **Perl**: `perl script.pl`
     * **R**: `Rscript script.R`
     * **Julia**: `julia script.jl`
     
     **Frontend Frameworks:**
     * **React**: `npm start` or `npm run dev` or `yarn start` or `pnpm dev` or `npm run build` or `npm test` or `npm run lint`
     * **Vue.js**: `npm run serve` or `npm run dev` or `vue-cli-service serve` or `vue-cli-service build` or `vue-cli-service test:unit` or `vite` or `vite build` or `vite preview`
     * **Angular**: `ng serve` or `npm start` or `ng build` or `ng test` or `ng lint` or `ng generate component`
     * **Next.js**: `npm run dev` or `next dev` or `npm run build` or `next build` or `next start` or `next lint` or `next export`
     * **Nuxt.js**: `npm run dev` or `nuxt dev` or `nuxt build` or `nuxt generate` or `nuxt start` or `nuxt analyze` or `nuxt typecheck`
     * **Svelte**: `npm run dev` or `svelte-kit dev` or `svelte-kit build` or `svelte-kit preview`
     * **Remix**: `npm run dev` or `remix dev` or `remix build` or `remix start`
     * **Vite**: `npm run dev` or `vite dev` or `vite build` or `vite preview` or `vite optimize` or `vite --host` or `vite --port 3000`
     * **Webpack**: `npm run build` or `webpack --mode development` or `webpack --mode production` or `webpack --watch`
     * **Parcel**: `parcel index.html` or `npm run build` or `parcel build` or `parcel watch`
     
     **Build Tools & Package Managers:**
     * **Go modules**: `go mod init`, `go mod tidy`, `go mod download`, `go mod vendor`, `go mod verify`, `go get <package>`, `go get -u <package>`, `go get -u ./...`, `go install <package>`
     * **npm**: `npm install`, `npm install <package>`, `npm install -D <package>`, `npm install -g <package>`, `npm uninstall <package>`, `npm update`, `npm update <package>`, `npm run <script>`, `npm test`, `npm start`, `npm run build`, `npm run lint`, `npm run dev`, `npm audit`, `npm audit fix`, `npm outdated`, `npm list`, `npm list --depth=0`
     * **yarn**: `yarn install`, `yarn add <package>`, `yarn add -D <package>`, `yarn add -g <package>`, `yarn remove <package>`, `yarn upgrade`, `yarn upgrade <package>`, `yarn run <script>`, `yarn test`, `yarn start`, `yarn build`, `yarn lint`, `yarn dev`, `yarn outdated`, `yarn list`, `yarn why <package>`
     * **pnpm**: `pnpm install`, `pnpm add <package>`, `pnpm add -D <package>`, `pnpm add -g <package>`, `pnpm remove <package>`, `pnpm update`, `pnpm update <package>`, `pnpm run <script>`, `pnpm test`, `pnpm start`, `pnpm build`, `pnpm lint`, `pnpm dev`, `pnpm outdated`, `pnpm list`
     * **pip**: `pip install -r requirements.txt`, `pip install <package>`, `pip install -U <package>`, `pip uninstall <package>`, `pip list`, `pip show <package>`, `pip freeze`, `pip freeze > requirements.txt`
     * **poetry**: `poetry install`, `poetry add <package>`, `poetry add -D <package>`, `poetry remove <package>`, `poetry update`, `poetry update <package>`, `poetry run python script.py`, `poetry run pytest`, `poetry show`, `poetry show <package>`, `poetry lock`, `poetry export -f requirements.txt`
     * **pipenv**: `pipenv install`, `pipenv install <package>`, `pipenv install -d <package>`, `pipenv uninstall <package>`, `pipenv update`, `pipenv run python script.py`, `pipenv shell`, `pipenv lock`
     * **cargo**: `cargo build`, `cargo run`, `cargo test`, `cargo add <package>`, `cargo remove <package>`, `cargo update`, `cargo check`, `cargo clippy`, `cargo fmt`
     * **maven**: `mvn compile`, `mvn test`, `mvn package`, `mvn install`, `mvn clean`, `mvn clean install`, `mvn dependency:tree`, `mvn dependency:resolve`
     * **gradle**: `gradle build`, `gradle test`, `gradle run`, `gradle clean`, `gradle dependencies`, `gradle tasks`
     * **composer**: `composer install`, `composer require <package>`, `composer require --dev <package>`, `composer remove <package>`, `composer update`, `composer update <package>`, `composer dump-autoload`, `composer validate`, `composer show`, `composer show <package>`, `composer test` (Laravel: `composer test` or `php artisan test`)
     * **bundler**: `bundle install`, `bundle add <package>`, `bundle remove <package>`, `bundle update`, `bundle update <package>`, `bundle exec ruby script.rb`, `bundle exec <command>`
     * **mix**: `mix deps.get`, `mix deps.update`, `mix deps.update <package>`, `mix compile`, `mix test`, `mix phx.server` (Phoenix), `mix ecto.migrate` (Phoenix)
     
     **Testing Frameworks:**
     * **Jest**: `npm test` or `jest` or `jest --watch`
     * **Mocha**: `npm test` or `mocha` or `mocha --watch`
     * **Vitest**: `npm test` or `vitest` or `vitest --watch`
     * **pytest**: `pytest` or `pytest -v` or `pytest --watch`
     * **unittest**: `python -m unittest` or `python -m unittest discover`
     * **JUnit**: `mvn test` or `gradle test`
     * **RSpec**: `rspec` or `bundle exec rspec`
     * **PHPUnit**: `phpunit` or `vendor/bin/phpunit`
     
     **Other Tools:**
     * **Docker**: `docker build .`, `docker run image`, `docker-compose up`
     * **SQL**: `psql -f script.sql` or `mysql < script.sql` or `sqlite3 db.sqlite < script.sql`
     * **Make**: `make` or `make build` or `make test`
     * **CMake**: `cmake . && make` or `cmake --build .`
     
   - Prefer POSIX shell commands (bash) for cross-platform compatibility
   - Check exit codes and stderr for errors
   - Examples: `execute_cmd("go run main.go")`, `execute_cmd("python script.py")`, `execute_cmd("npm test")`, `execute_cmd("docker build .")`
   - **IMPORTANT**: When user asks to run a file, use `execute_cmd` tool directly with the appropriate command for that language. Do NOT create shell script files unless the user explicitly asks for it.
   - **AUTO-EXECUTE SUGGESTED COMMANDS**: When you suggest or mention a bash/shell command in your response (especially in markdown code blocks like `\`\`\`bash`), you MUST automatically execute it using the `execute_cmd` tool. Do NOT just show the command - actually run it!
     * Examples of when to auto-execute:
       - If you say "You can start the application using: `go run main.go`" → immediately call `execute_cmd("go run main.go")`
       - If you write "Run this command: `npm install`" → immediately call `execute_cmd("npm install")`
       - If you mention "Use `php artisan serve` to start the server" → immediately call `execute_cmd("php artisan serve")`
       - If you provide a command in a code block like:
         \`\`\`bash
         go run main.go
         \`\`\`
         → immediately call `execute_cmd("go run main.go")`
     * **Rule**: Any bash/shell command you suggest or mention should be executed automatically. The user expects you to run commands, not just tell them what to run.
     * **Exception**: Only skip auto-execution if the user explicitly says "don't run it" or "just show me the command"

4. **Web Research** (via Research Subagent):
   - **IMPORTANT**: Use the `task` tool to delegate research to the `research-agent` subagent (if available)
   - The research subagent specializes in finding information from the web using Tavily search
   - **How to use**: Use `task(name="research-agent", task="your research question here")`
   - **When to delegate to research-agent**:
     * **ALWAYS delegate if you don't have the information** - Don't guess or make up answers!
     * **ALWAYS delegate if you're uncertain** - Better to search than to give wrong information
     * **ALWAYS delegate for current/up-to-date information** - Your training data may be outdated
     * **ALWAYS delegate when user asks about:**
       - Specific libraries, frameworks, or tools you're not familiar with
       - Recent changes, updates, or new features
       - Error messages or bugs you haven't seen before
       - Best practices or patterns you're unsure about
       - Documentation or tutorials for specific technologies
       - Current prices, news, or real-time information (e.g., "gold price today")
   - **Workflow when you don't know something:**
     1. Acknowledge that you need to search for information
     2. Immediately delegate to research-agent: `task(name="research-agent", task="Find information about X")`
     3. Wait for the subagent to return research results
     4. Use the results to provide an accurate answer to the user
     5. Cite the sources provided by the subagent
   - **Examples**:
     * `task(name="research-agent", task="Find Python async await best practices and tutorials")`
     * `task(name="research-agent", task="Research React hooks best practices with examples")`
     * `task(name="research-agent", task="Find solutions for ModuleNotFoundError in Python")`
     * `task(name="research-agent", task="Tìm thông tin về lỗi Python và cách khắc phục")`
     * `task(name="research-agent", task="What is the current gold price today?")`
   - **DO NOT:**
     - Try to run research commands via `execute_cmd` - use the subagent instead!
     - Guess or make up information
     - Say "I don't know" without delegating to research-agent first
     - Provide outdated information when current info is available via research
     - Skip research if the information is critical to the user's question
   - **Benefits of using research subagent**:
     * Keeps your context clean (research details stay in subagent)
     * Specialized in web search and information synthesis
     * Returns concise, cited results
     * Can handle complex multi-query research tasks

5. **Planning**:
   - For multi-step tasks, use `write_todos` to plan your approach
   - Break down complex tasks into manageable steps
   - Update todos as you complete each step

6. **Best Practices**:
   - Always read files before editing them
   - Prefer `edit_file` over `write_file` for modifications
   - **Auto-execute commands you suggest**: If you mention or suggest a bash/shell command in your response, automatically execute it using the `execute_cmd` tool. Don't just tell the user what command to run - actually run it for them!
   - **Research before guessing**: If you don't know something or are uncertain, delegate to research-agent subagent to find accurate information. Never make up or guess information when you can research it.
   - **Respect user rejections**: If user rejects a tool call, STOP immediately and ask what they want instead. Never retry the same operation or continue with the task after a rejection.
   - When asked to run a program/file, detect the language and use `execute_cmd` tool directly:
     * Check file extension (.go, .py, .js, .ts, .jsx, .tsx, .rs, .java, .cs, .rb, .php, .scala, .kt, .ex, .erl, .c, .cpp, .swift, .dart, .lua, .pl, .r, .jl, etc.)
     * Check for project files:
       - Go: go.mod, go.sum
       - Node.js: package.json, package-lock.json, yarn.lock, pnpm-lock.yaml
       - Python: requirements.txt, setup.py, pyproject.toml, Pipfile, poetry.lock
       - Rust: Cargo.toml, Cargo.lock
       - Java: pom.xml, build.gradle, settings.gradle
       - C#: *.csproj, *.sln
       - Ruby: Gemfile, Gemfile.lock
       - PHP: composer.json, composer.lock, artisan (Laravel), .env (Laravel), app/ (Laravel), routes/ (Laravel)
       - Elixir: mix.exs
       - Frontend: package.json, vite.config.js, vite.config.ts, webpack.config.js, next.config.js, nuxt.config.js, nuxt.config.ts, vue.config.js, angular.json, svelte.config.js
       - Laravel: artisan, app/, routes/, config/, database/migrations/, .env, composer.json
       - Nuxt: nuxt.config.js, nuxt.config.ts, pages/, components/, layouts/
       - Vue: vue.config.js, vite.config.js, vite.config.ts, src/, public/
     * Run the appropriate command directly: `execute_cmd("go run main.go")` NOT `write_file("run.sh", ...)`
   - Run tests after making changes (when execute tool is available)
   - Ask for clarification if requirements are unclear

## Human-in-the-Loop (HITL) - Understanding User Decisions

Some operations require user approval before execution. You will see messages like:
- "User approved the tool call for `edit_file`" - The operation was executed successfully
- "User rejected the tool call for `edit_file`" - The operation was NOT executed

**CRITICAL: When user REJECTS a tool call:**
- **STOP immediately** - Do NOT try to perform the same operation again
- **Do NOT continue with the task** - The user has explicitly said "no" to this action
- **Ask the user what they want instead** - Understand why they rejected and what they prefer
- **Do NOT retry with different parameters** - Respect the user's decision
- **Acknowledge the rejection** - Say something like "I understand you don't want me to make that change. What would you like me to do instead?"

**When user APPROVES a tool call:**
- Continue with the task normally
- The operation was executed successfully

**When user EDITS a tool call:**
- The operation was executed with modified parameters
- Continue with the task using the edited parameters

**Examples:**

❌ **WRONG** (after rejection):
```
User: sửa nội dung của nó thêm text hello
[User rejected edit_file]
Agent: Mình sẽ chỉnh sửa file a.md để thêm chữ "Hello"...
[Agent tries again - WRONG!]
```

✅ **CORRECT** (after rejection):
```
User: sửa nội dung của nó thêm text hello
[User rejected edit_file]
Agent: Tôi hiểu bạn không muốn tôi chỉnh sửa file theo cách đó. Bạn muốn tôi làm gì thay thế? 
Có thể bạn muốn:
- Thêm "Hello" ở vị trí khác?
- Sử dụng cách khác để thêm text?
- Hoặc bạn có yêu cầu khác?
```

## Workflow Example

When asked to fix a bug:
1. Use `write_todos` to plan: identify bug → read relevant files → implement fix → test
2. Use `read_file` to examine the problematic code
3. If you don't know the solution, delegate to research-agent: `task(name="research-agent", task="Find solutions for [bug description]")`
4. Use `edit_file` to apply the fix
5. **If user rejects the edit**: Stop, ask what they want instead, do NOT retry
6. Use `execute_cmd` to run tests and verify the fix
7. Mark the todo as completed
8. Summarize what you did

When asked about something you don't know:
1. **DO NOT guess or make up information**
2. Immediately delegate to research-agent: `task(name="research-agent", task="your research question")`
3. Wait for subagent to return results
4. Review the research results from subagent
5. Provide answer based on the research, citing sources from subagent
6. If still unclear, delegate again with a more specific question

Example:
- User: "How do I use the new React 19 features?"
- Agent: [Delegates to research-agent: task(name="research-agent", task="Find information about React 19 new features and how to use them")]
- Agent: [Receives research results from subagent]
- Agent: [Provides answer based on research, citing sources]

When suggesting commands to the user:
- **WRONG**: "You can start the application using: `go run main.go`" (just telling, not doing)
- **CORRECT**: 
  1. Say "Starting the application..." 
  2. Immediately call `execute_cmd("go run main.go")`
  3. Show the results
  
- **WRONG**: Writing a code block with a command and expecting user to run it:
  \`\`\`bash
  go run /home/son/work/hello/main.go
  \`\`\`
  
- **CORRECT**: 
  1. Write the explanation
  2. Immediately execute: `execute_cmd("go run /home/son/work/hello/main.go")`
  3. Show the execution results

**Remember**: If you mention a command, you must run it. The user expects action, not just instructions!

Remember: You are working in a sandboxed environment. Stay focused, be methodical, and
always verify your changes fit within the workspace constraints.
"""


def build_agent(
    workspace: Path,
    model_id: str = "openai:gpt-4.1-mini",
    system_prompt: Optional[str] = None,
    verbose: bool = False,
    max_command_timeout: int = 300,
    enable_hitl: bool = True,
):
    """
    Build a DeepAgent configured for the workspace.
    
    Args:
        workspace: Absolute path to workspace directory
        model_id: Model identifier (e.g., "openai:gpt-4o")
        system_prompt: Custom system prompt (uses default if None)
        verbose: Enable verbose logging
        max_command_timeout: Maximum timeout for shell commands in seconds
        enable_hitl: Enable human-in-the-loop approval for sensitive operations
        
    Returns:
        Compiled LangGraph agent
    """
    # Create workspace backend
    backend = create_workspace_backend(workspace)
    
    # Create shell executor
    executor = create_executor(
        workspace=workspace,
        default_timeout=max_command_timeout,
    )
    
    # Create execute tool
    @tool
    def execute_cmd(command: str, timeout: Optional[int] = None) -> str:
        """
        Execute a shell command in the workspace directory.
        
        Use this to run commands directly - DO NOT create shell script files unless explicitly requested.
        The command runs in a POSIX shell (bash preferred) on all platforms when available.
        
        When user asks to run a file, detect the language and use the appropriate command:
        
        Backend: Go (go run/go mod), Python (python/pytest), Node.js/TypeScript (node/npm/yarn/pnpm), Java (mvn/gradle),
        C# (.NET: dotnet), Rust (cargo), Ruby (ruby/bundle), PHP (php/composer/Laravel artisan), Scala (sbt),
        Kotlin (kotlinc/gradle), Elixir (mix), C/C++ (gcc/make), Swift (swift), Dart (dart)
        
        Frontend: React/Vue.js/Angular/Next.js/Nuxt.js (npm/yarn/pnpm), Vite, Webpack, Parcel, Svelte, Remix
        
        Frameworks: Laravel (php artisan), Nuxt.js (nuxt dev/nuxt build), Vue.js (vue-cli/vite), Next.js (next dev/next build)
        
        Testing: Jest, Mocha, Vitest, pytest, unittest, JUnit, RSpec, PHPUnit, Laravel (php artisan test)
        
        Build tools: npm/yarn/pnpm (install/add/remove/update), pip/poetry/pipenv, cargo, maven/gradle, composer (require/update), bundler, go mod
        
        Args:
            command: Shell command to execute (e.g., "go run main.go", "python script.py", "npm test", "docker build .")
            timeout: Optional timeout in seconds (default: 300)
            
        Returns:
            Command output including stdout, stderr, exit code, and execution time.
            
        Examples:
            execute_cmd("go run main.go")
            execute_cmd("go mod tidy")
            execute_cmd("python script.py --arg value")
            execute_cmd("npm run dev")
            execute_cmd("npm install vue")
            execute_cmd("yarn add axios")
            execute_cmd("pnpm install")
            execute_cmd("pytest -v")
            execute_cmd("cargo run")
            execute_cmd("docker build .")
            execute_cmd("mvn test")
            execute_cmd("composer install")
            execute_cmd("composer require laravel/sanctum")
            execute_cmd("php artisan serve")
            execute_cmd("php artisan migrate")
            execute_cmd("php artisan test")
            execute_cmd("nuxt dev")
            execute_cmd("nuxt build")
            execute_cmd("vite dev")
            execute_cmd("vite build")
            execute_cmd("vue-cli-service serve")
        """
        result = executor.execute(command, timeout=timeout)
        
        # Format result as a readable string
        output = f"Command: {result.command}\n"
        output += f"Exit Code: {result.exit_code}\n"
        output += f"Duration: {result.duration_ms}ms\n"
        print(f"[Agent] Command: \n{output}")
        

        if result.timed_out:
            output += f"\n⚠️ Command timed out!\n"
        
        if result.truncated:
            output += f"\n⚠️ Output was truncated (too large)\n"
        
        if result.stdout:
            output += f"\n--- STDOUT ---\n{result.stdout}\n"
        
        if result.stderr:
            output += f"\n--- STDERR ---\n{result.stderr}\n"
        
        return output
    
    # Create read_image tool
    @tool
    def read_image(path: str, prompt: str = "Mô tả chi tiết nội dung của ảnh này") -> str:
        """
        Đọc và phân tích nội dung file ảnh (png, jpg, jpeg, svg, gif, webp) bằng vision model.
        
        Tool này sử dụng AI vision model để "xem" và mô tả nội dung ảnh, bao gồm:
        - Mô tả các đối tượng trong ảnh
        - Text có trong ảnh (OCR)
        - Màu sắc, bố cục, thiết kế
        - Biểu đồ, charts, diagrams
        - UI/UX elements nếu là screenshot
        
        Args:
            path: Đường dẫn file ảnh (png, jpg, jpeg, svg, gif, webp)
            prompt: Câu hỏi hoặc yêu cầu về ảnh (mặc định: mô tả chi tiết)
            
        Returns:
            Phân tích và mô tả nội dung ảnh từ AI
            
        Examples:
            read_image("screenshot.png")
            read_image("diagram.jpg", "Giải thích biểu đồ này")
            read_image("ui.png", "Phân tích UI design của màn hình này")
        """
        try:
            # Validate file path
            file_path = Path(path)
            if not file_path.is_absolute():
                file_path = workspace / file_path
            
            file_path = file_path.resolve()
            if not str(file_path).startswith(str(workspace.resolve())):
                return f"❌ Error: Path outside workspace: {path}"
            
            if not file_path.exists():
                return f"❌ Error: Image file not found: {path}"
            
            # Check if it's an image file
            valid_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp'}
            if file_path.suffix.lower() not in valid_extensions:
                return f"❌ Error: Unsupported image format: {file_path.suffix}. Supported: {', '.join(valid_extensions)}"
            
            # Read and encode image
            with open(file_path, 'rb') as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Determine image type
            image_type = file_path.suffix.lower().replace('.', '')
            if image_type == 'jpg':
                image_type = 'jpeg'
            
            # Get vision model from environment or use default
            vision_model_id = os.getenv("VISION_MODEL", "openai:gpt-4o-mini")
            vision_model = init_chat_model(vision_model_id)
            
            # Create message with image
            message = HumanMessage(
                content=[
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/{image_type};base64,{image_data}"
                        }
                    }
                ]
            )
            
            # Call vision model
            response = vision_model.invoke([message])
            
            # Format response
            result = f"📷 Image: {file_path.relative_to(workspace)}\n"
            result += f"📏 Size: {file_path.stat().st_size} bytes\n"
            result += f"🤖 Vision Model: {vision_model_id}\n"
            result += f"\n--- AI Analysis ---\n"
            result += response.content
            
            return result
            
        except Exception as e:
            error_msg = str(e)
            vision_model_id = os.getenv("VISION_MODEL", "openai:gpt-4o-mini")
            if "does not support" in error_msg.lower() or "vision" in error_msg.lower():
                return f"❌ Error: Model {vision_model_id} không hỗ trợ vision. Hãy dùng model có vision capability như 'openai:gpt-4o' hoặc 'openai:gpt-4o-mini'"
            return f"❌ Error: {error_msg}"
    
    # Create tavily_research tool (conditional on API key and library availability)
    tavily_research = None
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    
    if TAVILY_AVAILABLE and tavily_api_key:
        @tool
        def tavily_research(
            query: str,
            depth: str = "medium",
            max_results: int = 5,
            language: str = "en"
        ) -> str:
            """
            Tìm kiếm và nghiên cứu thông tin từ web sử dụng Tavily API.
            
            Tool này cho phép agent tìm kiếm thông tin mới nhất từ internet, bao gồm:
            - Documentation và tutorials
            - Best practices và coding patterns
            - Giải pháp cho bugs và errors
            - Thông tin về libraries, frameworks mới
            - Technical articles và blog posts
            
            Args:
                query: Câu hỏi hoặc từ khóa tìm kiếm (ví dụ: "Python async best practices", "React hooks tutorial")
                depth: Độ sâu tìm kiếm - "basic" (nhanh, ít kết quả), "medium" (cân bằng), "advanced" (sâu, nhiều kết quả)
                max_results: Số lượng kết quả tối đa (1-20, mặc định: 5)
                language: Ngôn ngữ kết quả - "en" (English), "vi" (Vietnamese), "es", "fr", etc. (mặc định: "en")
                
            Returns:
                Kết quả tìm kiếm được format với:
                - Tổng quan về chủ đề
                - Danh sách các sources với URLs
                - Nội dung tóm tắt từ các sources
                - Key insights và takeaways
                
            Examples:
                tavily_research("Python async await best practices")
                tavily_research("React hooks tutorial", depth="advanced", max_results=10)
                tavily_research("Lỗi ModuleNotFoundError Python", language="vi")
            """
            try:
                # Validate query
                query = query.strip()
                if not query:
                    return "❌ Error: Query cannot be empty"
                
                # Validate depth
                valid_depths = {"basic", "medium", "advanced"}
                if depth not in valid_depths:
                    return f"❌ Error: Invalid depth '{depth}'. Must be one of: {', '.join(valid_depths)}"
                
                # Validate max_results
                if not isinstance(max_results, int) or max_results < 1 or max_results > 20:
                    return f"❌ Error: max_results must be an integer between 1 and 20, got: {max_results}"
                
                # Validate language (basic check for common codes)
                language = language.strip().lower()
                if len(language) != 2:
                    return f"❌ Error: Language code must be 2 characters (e.g., 'en', 'vi'), got: {language}"
                
                # Map depth to Tavily search_depth
                # Tavily only supports "basic" and "advanced", so map "medium" to "advanced"
                search_depth = "advanced" if depth in ("medium", "advanced") else "basic"
                
                # Initialize Tavily client
                tavily_client = TavilyClient(api_key=tavily_api_key)
                
                # Perform search
                response = tavily_client.search(
                    query=query,
                    search_depth=search_depth,
                    max_results=max_results,
                    include_answer=True,
                    include_raw_content=False,
                )
                
                # Format response
                result = f"📚 Research Results: \"{query}\"\n\n"
                result += f"🔍 Search Parameters:\n"
                result += f"- Depth: {depth} (Tavily: {search_depth})\n"
                result += f"- Max Results: {max_results}\n"
                result += f"- Language: {language}\n\n"
                
                # Add summary/answer if available
                if response.get("answer"):
                    result += f"📊 Summary:\n{response['answer']}\n\n"
                
                # Add sources
                results = response.get("results", [])
                if results:
                    result += f"📝 Sources ({len(results)}):\n"
                    for i, source in enumerate(results, 1):
                        title = source.get("title", "Untitled")
                        url = source.get("url", "No URL")
                        content = source.get("content", "")
                        
                        # Truncate content to 500 chars
                        if len(content) > 500:
                            content = content[:500] + "..."
                        
                        result += f"{i}. {title}\n"
                        result += f"   URL: {url}\n"
                        if content:
                            result += f"   Content: {content}\n"
                        result += "\n"
                    
                    # Add key insights from top results
                    if len(results) > 0:
                        result += "💡 Key Insights:\n"
                        # Extract insights from top 3 results
                        for i, source in enumerate(results[:3], 1):
                            title = source.get("title", "")
                            if title:
                                result += f"- {title}\n"
                else:
                    result += "📝 No sources found.\n\n"
                
                # Add follow-up questions if available
                follow_ups = response.get("follow_up_questions", [])
                if follow_ups:
                    result += "❓ Suggested Follow-up Questions:\n"
                    for question in follow_ups[:3]:  # Limit to 3
                        result += f"- {question}\n"
                
                # Truncate if too long (max 8000 chars to avoid context overflow)
                if len(result) > 8000:
                    result = result[:8000] + "\n\n⚠️ Response truncated due to length limit."
                
                return result
                
            except Exception as e:
                error_msg = str(e)
                # Handle specific errors
                if "api key" in error_msg.lower() or "authentication" in error_msg.lower():
                    return "❌ Error: Invalid or missing TAVILY_API_KEY. Please check your API key."
                elif "rate limit" in error_msg.lower() or "429" in error_msg:
                    return "❌ Error: Tavily API rate limit exceeded. Please try again later."
                elif "network" in error_msg.lower() or "connection" in error_msg.lower():
                    return "❌ Error: Network error connecting to Tavily API. Please check your internet connection."
                else:
                    return f"❌ Error: {error_msg}"
    
    # Initialize model
    model = init_chat_model(model_id)
    
    # Use custom prompt or default
    prompt = system_prompt or DEFAULT_SYSTEM_PROMPT
    
    # Add workspace context to prompt
    workspace_context = f"\n\n## Current Workspace\n\nYou are working in: `{workspace}`\n"
    workspace_context += f"Shell: {executor.shell_type.value}\n"
    full_prompt = prompt + workspace_context
    
    # Create checkpointer for state persistence
    checkpointer = MemorySaver()
    
    # Configure HITL (Human-in-the-loop) for sensitive operations
    interrupt_config = {}
    if enable_hitl:
        interrupt_config = {
            # File creation/overwrite - allow approve, edit, or reject
            # "write_file": {"allowed_decisions": ["approve", "edit", "reject"]},
            # File editing - allow approve, edit, or reject
            "edit_file": {"allowed_decisions": ["approve", "edit", "reject"]},
            # Shell execution - allow approve, edit, or reject
            "execute_cmd": {"allowed_decisions": ["approve", "edit", "reject"]},
        }
        # Optional: Require approval for tavily_research (uncomment if needed)
        # Note: tavily_research runs without approval by default for convenience
        # If you want to control web searches, uncomment the line below:
        # if tavily_research is not None:
        #     interrupt_config["tavily_research"] = {"allowed_decisions": ["approve", "edit", "reject"]}
    
    # Build tools list (tavily_research moved to subagent)
    tools = [execute_cmd, read_image]
    
    # Create research subagent with tavily_research tool
    subagents = []
    if tavily_research is not None:
        if verbose:
            print(f"[Agent] Creating research-agent subagent with tavily_research tool")
        research_subagent = {
            "name": "research-agent",
            "description": "Chuyên gia tìm kiếm và nghiên cứu thông tin từ web. Sử dụng khi cần tìm kiếm documentation, tutorials, best practices, giải pháp cho bugs/errors, hoặc thông tin mới nhất về libraries/frameworks/technologies.",
            "system_prompt": """Bạn là chuyên gia nghiên cứu và tìm kiếm thông tin.

## Nhiệm vụ của bạn

- Tìm kiếm thông tin chính xác từ web sử dụng `tavily_research` tool
- Phân tích và tổng hợp thông tin từ nhiều nguồn
- Trích dẫn nguồn rõ ràng với URLs
- Đưa ra câu trả lời súc tích và hữu ích

## Tool có sẵn

Bạn có `tavily_research` tool với các parameters:
- `query`: Câu hỏi tìm kiếm (bắt buộc)
- `depth`: "basic" (nhanh), "medium" (cân bằng), "advanced" (chi tiết)
- `max_results`: Số lượng kết quả (1-20, mặc định: 5)
- `language`: Mã ngôn ngữ ("en", "vi", etc.)

## Workflow

1. Phân tích yêu cầu của main agent
2. Tạo search queries phù hợp (có thể nhiều queries cho câu hỏi phức tạp)
3. Gọi `tavily_research` tool để tìm kiếm
4. Tổng hợp kết quả từ các sources
5. Trả về báo cáo ngắn gọn, chính xác với citations

## Lưu ý quan trọng

- **Luôn trích dẫn nguồn** với URLs
- **Tìm kiếm nhiều lần** nếu câu hỏi phức tạp
- **Đảm bảo thông tin chính xác** - không đoán hoặc bịa
- **Tóm tắt ngắn gọn** - main agent cần thông tin súc tích
- **Sử dụng ngôn ngữ phù hợp** - nếu user hỏi bằng tiếng Việt, set language="vi"

Hãy tìm kiếm thông tin chính xác và trả về kết quả hữu ích!""",
            "tools": [tavily_research],
            "model": model_id,  # Use same model as main agent
        }
        subagents.append(research_subagent)
    else:
        if verbose:
            if not TAVILY_AVAILABLE:
                print(f"[Agent] Warning: tavily-python not installed - research-agent subagent not available")
            elif not tavily_api_key:
                print(f"[Agent] Warning: TAVILY_API_KEY not set - research-agent subagent not available")
    
    # Create DeepAgent with workspace backend and tools
    agent = create_deep_agent(
        model=model,
        backend=lambda runtime: backend,  # Provide backend factory
        system_prompt=full_prompt,
        checkpointer=checkpointer,
        tools=tools,
        subagents=subagents,  # Add research subagent
        interrupt_on=interrupt_config,  # HITL configuration
    )
    
    if verbose:
        print(f"[Agent] Initialized with model: {model_id}")
        print(f"[Agent] Workspace: {workspace}")
        print(f"[Agent] Backend: WorkspaceFilesystemBackend")
        print(f"[Agent] Shell: {executor.shell_type.value}")
        tool_names = ["execute_cmd", "read_image"]
        print(f"[Agent] Tools: {', '.join(tool_names)} + filesystem tools")
        print(f"[Agent] HITL: {'enabled' if enable_hitl else 'disabled'}")
        
        # Show subagents info
        if subagents:
            print(f"[Agent] Subagents: {len(subagents)}")
            for subagent in subagents:
                print(f"  - {subagent['name']}: {subagent['description'][:60]}...")
        else:
            if not TAVILY_AVAILABLE:
                print(f"[Agent] Research: tavily-python not installed (optional dependency)")
            elif not tavily_api_key:
                print(f"[Agent] Research: TAVILY_API_KEY not set (optional)")
    
    return agent


def create_session_config(thread_id: Optional[str] = None) -> dict:
    """
    Create configuration for agent session.
    
    Args:
        thread_id: Optional thread ID for conversation persistence
        
    Returns:
        Config dict for agent.invoke()
    """
    import uuid
    
    if not thread_id:
        thread_id = str(uuid.uuid4())
    
    return {
        "configurable": {
            "thread_id": thread_id,
        }
    }

