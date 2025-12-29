import sys
import argparse
import time
from pathlib import Path
from fabriq.rag_pipeline import RAGPipeline
from fabriq.indexing import DocumentIndexer
from fabriq.config_parser import ConfigParser
import threading
import logging

# --- ANSI color codes ---
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
UNDERLINE = "\033[4m"
CYAN = "\033[36m"
YELLOW = "\033[33m"
GREEN = "\033[32m"
RED = "\033[31m"
MAGENTA = "\033[35m"
BLUE = "\033[34m"
WHITE = "\033[97m"
GRAY = "\033[90m"
BG_BLUE = "\033[44m"
BG_CYAN = "\033[46m"
BG_MAGENTA = "\033[45m"

# Silence all logs lower than ERROR
logging.getLogger().setLevel(logging.ERROR)
logging.getLogger("openai").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)

class ChatbotCLI:
    def __init__(self, config_path="config/config.yaml"):
        print(f"{CYAN}{BOLD}🔧 Loading configuration...{RESET}")
        self.config = ConfigParser(config_path)
        
        print(f"{CYAN}{BOLD}🤖 Initializing chatbot...{RESET}")
        self.chatbot = RAGPipeline(self.config)
        self.indexer = DocumentIndexer(self.config)
        
        self.history = []
        print(f"{GREEN}{BOLD}✅ Chatbot ready!{RESET}\n")
    
    def print_banner(self):
        banner = f"""
{BOLD}{CYAN}╔{'═'*58}╗
║{RESET}{BOLD}{MAGENTA}               FABRIQ CHATBOT{RESET}{CYAN}{' ' * 29}║
╠{'═'*58}╣
║{RESET}  {YELLOW}Commands:{RESET}{' '*47}{CYAN}║
║{RESET}    {GREEN}/help{RESET}     - Show this help message{' '*20}{CYAN}║
║{RESET}    {GREEN}/clear{RESET}    - Clear conversation history{' '*16}{CYAN}║
║{RESET}    {GREEN}/history{RESET}  - Show conversation history{' '*17}{CYAN}║
║{RESET}    {GREEN}/upload{RESET}   - Upload documents from a directory{' '*9}{CYAN}║
║{RESET}    {GREEN}/exit{RESET}     - Exit the chatbot{' '*26}{CYAN}║
║{RESET}    {GREEN}/quit{RESET}     - Exit the chatbot{' '*26}{CYAN}║
╠{'═'*58}╣
║{RESET}  {BOLD}Type your message and press Enter to chat.{RESET}{' '*14}{CYAN}║
╚{'═'*58}╝{RESET}
"""
        print(banner)
    
    def stream_response(self, prompt, delay=0.01):
        def loading_cursor(stop_event):
            cursor = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
            idx = 0
            while not stop_event.is_set():
                print(f"\r{MAGENTA}🤖 Assistant: Thinking... {cursor[idx % len(cursor)]}{RESET}", end="", flush=True)
                idx += 1
                time.sleep(0.1)
        
        stop_event = threading.Event()
        loader_thread = threading.Thread(target=loading_cursor, args=(stop_event,), daemon=True)
        loader_thread.start()
        
        try:
            response = self.chatbot.get_response(prompt, stream=True)
            text_chunks = response.get("text", [])
            chunk_iterator = iter(text_chunks)
            try:
                first_chunk = next(chunk_iterator)
                stop_event.set()
                loader_thread.join(timeout=0.5)
                print(f"\r\033[K{MAGENTA}{BOLD}🤖 Assistant:{RESET} ", end="", flush=True)
                text = getattr(first_chunk, "content", first_chunk)
                full_response = [text]
                for ch in text:
                    print(f"{CYAN}{ch}{RESET}", end="", flush=True)
                    time.sleep(delay)
                for chunk in chunk_iterator:
                    text = getattr(chunk, "content", chunk)
                    full_response.append(text)
                    for ch in text:
                        print(f"{CYAN}{ch}{RESET}", end="", flush=True)
                        time.sleep(delay)
            except StopIteration:
                stop_event.set()
                loader_thread.join(timeout=0.5)
                print(f"\r\033[K{RED}🤖 Assistant: (No response){RESET}\n")
                return ""
            print("\n")
            return "".join(full_response)
        except Exception as e:
            stop_event.set()
            loader_thread.join(timeout=0.5)
            print(f"\r\033[K{RED}❌ Error: {e}{RESET}\n")
            return ""
        finally:
            stop_event.set()
            if loader_thread.is_alive():
                loader_thread.join(timeout=0.5)
    
    def get_file_paths(self, dir_path):
        p = Path(dir_path)
        if not p.is_dir():
            raise ValueError(f"{RED}Provided path is not a directory: {dir_path}{RESET}")
        return [str(f) for f in p.glob("**/*") if f.is_file()]
    
    def upload_documents(self, dir_path):
        file_paths = self.get_file_paths(dir_path)
        if not file_paths:
            print(f"{YELLOW}No files found in directory: {dir_path}{RESET}")
            return
        print(f"{CYAN}📂 Uploading {len(file_paths)} documents from {dir_path}...{RESET}")
        error_count = self.indexer.index_documents(file_paths)
        success_count = len(file_paths) - error_count
        if error_count == 0:
            print(f"{GREEN}✅ All documents uploaded and indexed successfully!{RESET}\n")
        elif success_count == 0:
            print(f"{RED}❌ Failed to index all {len(file_paths)} documents. Check error_files.xlsx{RESET}\n")
        else:
            print(f"{YELLOW}⚠️  Indexed {success_count}/{len(file_paths)} documents successfully.{RESET}")
            print(f"{RED}   {error_count} failed. Check error_files.xlsx for details.{RESET}\n")
    
    def show_history(self):
        if not self.history:
            print(f"\n{GRAY}📜 No conversation history yet.{RESET}\n")
            return
        print(f"\n{BOLD}{CYAN}📜 Conversation History:{RESET}")
        print(f"{CYAN}{'─'*60}{RESET}")
        for i, msg in enumerate(self.history, 1):
            role = f"{GREEN}👤 You{RESET}" if msg["role"] == "user" else f"{MAGENTA}🤖 Assistant{RESET}"
            print(f"\n{role}:")
            print(f"{WHITE}{msg['content']}{RESET}")
            if i < len(self.history):
                print(f"{CYAN}{'─'*60}{RESET}")
        print()
    
    def clear_history(self):
        self.history.clear()
        print(f"\n{YELLOW}🗑️  Conversation history cleared.{RESET}\n")
    
    def handle_command(self, user_input):
        cmd = user_input.lower().strip()
        if cmd in ["/exit", "/quit"]:
            print(f"\n{BOLD}{CYAN}👋 Goodbye!{RESET}\n")
            return False
        elif cmd == "/help":
            self.print_banner()
        elif cmd == "/clear":
            self.clear_history()
        elif cmd == "/history":
            self.show_history()
        elif cmd == "/upload":
            dir_path = input(f"{YELLOW}📁 Enter directory path to upload documents: {RESET}").strip()
            try:
                self.upload_documents(dir_path)
            except Exception as e:
                print(f"\n{RED}❌ Error uploading documents: {e}{RESET}\n")
        else:
            print(f"\n{RED}❌ Unknown command: {user_input}{RESET}")
            print(f"{YELLOW}Type /help to see available commands.{RESET}\n")
        return True
    
    def run(self):
        self.print_banner()
        try:
            while True:
                try:
                    user_input = input(f"{GREEN}👤 You: {RESET}").strip()
                except EOFError:
                    print(f"\n{BOLD}{CYAN}👋 Goodbye!{RESET}\n")
                    break
                if not user_input:
                    continue
                if user_input.startswith("/"):
                    if not self.handle_command(user_input):
                        break
                    continue
                self.history.append({"role": "user", "content": user_input})
                try:
                    response = self.stream_response(user_input)
                    self.history.append({"role": "assistant", "content": response})
                except KeyboardInterrupt:
                    print(f"\n\n{YELLOW}⚠️  Response interrupted.{RESET}\n")
                    continue
                except Exception as e:
                    print(f"\n{RED}❌ Error getting response: {e}{RESET}\n")
                    continue
        except KeyboardInterrupt:
            print(f"\n\n{BOLD}{CYAN}👋 Goodbye!{RESET}\n")
        except Exception as e:
            print(f"\n{RED}❌ Fatal error: {e}{RESET}\n")
            sys.exit(1)


def main():
    """Entry point for the CLI tool"""
    parser = argparse.ArgumentParser(
        description="Chat with your Documents using Fabriq Chat CLI.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "--config",
        "-c",
        default="config/config.yaml",
        help="Path to configuration file (default: config/config.yaml)"
    )
    
    args = parser.parse_args()
    
    # Check if config file exists
    if not Path(args.config).exists():
        print(f"❌ Config file not found: {args.config}")
        sys.exit(1)
    
    # Initialize and run chatbot
    cli = ChatbotCLI(config_path=args.config)
    cli.run()


if __name__ == "__main__":
    main()