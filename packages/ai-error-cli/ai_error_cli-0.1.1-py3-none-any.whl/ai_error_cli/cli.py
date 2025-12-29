import sys
from ai_error_cli.executor import run_command
from ai_error_cli.ai_client import send_error_to_ai

RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
RESET = "\033[0m"
SEPARATOR = "───────────────────────────────────────────────────────────────────────────────────────────────────────────────"


def main():
    if len(sys.argv) < 2:
        print("Usage: ai-run <command>")
        sys.exit(1)

    command = sys.argv[1:]

    stdout, stderr = run_command(command)

    if stderr:
        print(f"\n{RED}❌ Error detected{RESET}")
        print(SEPARATOR)
        print(stderr.strip())
        
        print("|────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────|")
        print(f"|                                                                 {CYAN}🤖 AI Error Explanation{RESET}                                                        |")
        print("|────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────|")
        ai_response = send_error_to_ai(stderr)

        # Safety fallback
        if not ai_response or not any(ai_response.values()):
            ai_response = {
                "cause": "AI could not analyze this error.",
                "solution": "Check the traceback above or retry after some time.",
                "example": "Example could not be generated."
            }
            
        def safe_print(text):
            print(text if text else "⚠️ - No data returned by AI")
            
        print(SEPARATOR)
        print(f"{YELLOW}🧠 CAUSE:{RESET}")
        safe_print(ai_response.get("cause", ""))
        print(SEPARATOR)

        print(f"{GREEN}🛠️ SOLUTIONS:{RESET}")
        safe_print("\n".join(ai_response.get("solutions", [])))
        print(SEPARATOR)

        print(f"{BLUE}📌 EXAMPLE:{RESET}")
        safe_print(ai_response.get("example", ""))
        print(SEPARATOR)

        print(f"{GREEN}📝 POSSIBLE FIX STEPS:{RESET}")
        safe_print("\n".join(ai_response.get("possible_fix_steps", [])))
        print(SEPARATOR)

        print(f"{YELLOW}🔗 REFERENCES:{RESET}")
        safe_print("\n".join(ai_response.get("references", [])))
        print(SEPARATOR)

        print(f"{BLUE}💡 PREVENTIVE TIPS:{RESET}")
        safe_print("\n".join(ai_response.get("preventive_tips", [])))
        print(SEPARATOR)

        print(f"{CYAN}🖥️ CODE CONTEXT:{RESET}")
        safe_print(ai_response.get("code_context", ""))
        print(SEPARATOR)
        
        print(f"{CYAN}🔹 ERROR TYPE:{RESET} {ai_response.get('error_type', '')}")
        print(f"{CYAN}🤖 AI CONFIDENCE:{RESET} {ai_response.get('confidence', 0.0)}")
        print(SEPARATOR)

    else:
        print(stdout)


if __name__ == "__main__":
    main()
