/* The Windows release's exe: starts the patcher with the Python in
   _internal beside it, as

       _internal\pythonw.exe _internal\v-on-patcher.py [arguments]

   waits for it and returns its exit code. Everything the patcher does is
   in the script; this only finds it. The working directory is left as the
   caller's, so relative paths given as arguments mean what they did.

   pythonw has nowhere to print a traceback, so Python's stderr goes to a
   temporary file. If Python exits with an error and wrote to it, the text
   goes to this program's own stderr when that is a file or a pipe (a
   redirect, CI), and to a message box otherwise.

   The same signed build ships with every release, so its hash keeps the
   reputation it has earned. Nothing here depends on the patcher's
   version; see launcher.rc. */

#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <wchar.h>

#define LONG_PATH 32768
#define SHOWN 8192                      /* bytes of stderr a message box shows, from the end */

static wchar_t here[LONG_PATH];
static wchar_t python[LONG_PATH];
static wchar_t script[LONG_PATH];
static wchar_t command[LONG_PATH];
static wchar_t temp[MAX_PATH + 1];
static wchar_t name[MAX_PATH + 1];
static char tail[SHOWN + 1];
static wchar_t text[SHOWN + 128];

static int fail(const wchar_t *what)
{
    MessageBoxW(NULL, what, L"V-On Patcher", MB_OK | MB_ICONERROR);
    return 1;
}

/* The command line past the program's own name, per the rules Windows
   uses to split it: a quoted name runs to the closing quote, an unquoted
   one to the first blank. */
static const wchar_t *arguments(const wchar_t *line)
{
    if (*line == L'"') {
        for (line++; *line && *line != L'"'; line++)
            ;
        if (*line)
            line++;
    } else {
        while (*line && *line != L' ' && *line != L'\t')
            line++;
    }
    while (*line == L' ' || *line == L'\t')
        line++;
    return line;
}

static int present(const wchar_t *path)
{
    DWORD attributes = GetFileAttributesW(path);
    return attributes != INVALID_FILE_ATTRIBUTES
        && !(attributes & FILE_ATTRIBUTE_DIRECTORY);
}

/* A temporary file for Python's stderr, inherited by the child and gone
   when the last handle closes. INVALID_HANDLE_VALUE if there is none to
   be had; Python then runs without one, as pythonw does anyway. */
static HANDLE capture(void)
{
    SECURITY_ATTRIBUTES inherit = { sizeof inherit, NULL, TRUE };
    DWORD length = GetTempPathW(MAX_PATH + 1, temp);
    HANDLE file;

    if (length == 0 || length > MAX_PATH || !GetTempFileNameW(temp, L"von", 0, name))
        return INVALID_HANDLE_VALUE;
    file = CreateFileW(name, GENERIC_READ | GENERIC_WRITE, FILE_SHARE_READ | FILE_SHARE_WRITE,
                       &inherit, CREATE_ALWAYS,
                       FILE_ATTRIBUTE_TEMPORARY | FILE_FLAG_DELETE_ON_CLOSE, NULL);
    if (file == INVALID_HANDLE_VALUE)
        DeleteFileW(name);              /* the empty file GetTempFileNameW made */
    return file;
}

/* The last SHOWN bytes of what Python wrote to stderr, or 0 bytes. */
static DWORD collect(HANDLE file)
{
    LARGE_INTEGER size, from;
    DWORD got = 0;

    if (!GetFileSizeEx(file, &size) || size.QuadPart == 0)
        return 0;
    from.QuadPart = size.QuadPart > SHOWN ? size.QuadPart - SHOWN : 0;
    if (!SetFilePointerEx(file, from, NULL, FILE_BEGIN)
        || !ReadFile(file, tail, SHOWN, &got, NULL))
        return 0;
    return got;
}

static void report(DWORD got)
{
    HANDLE out = GetStdHandle(STD_ERROR_HANDLE);
    DWORD type = out && out != INVALID_HANDLE_VALUE ? GetFileType(out) : FILE_TYPE_UNKNOWN;
    DWORD written;
    int length, n;

    if (type == FILE_TYPE_DISK || type == FILE_TYPE_PIPE) {
        WriteFile(out, tail, got, &written, NULL);
        return;
    }
    /* Python writes a file's stderr in the ANSI code page. */
    n = swprintf(text, sizeof text / sizeof *text,
                 L"V-On Patcher stopped with an error. Ctrl+C copies this message.\n\n");
    if (n < 0)
        return;
    length = MultiByteToWideChar(CP_ACP, 0, tail, (int)got, text + n,
                                 (int)(sizeof text / sizeof *text) - n - 1);
    text[n + (length > 0 ? length : 0)] = L'\0';
    MessageBoxW(NULL, text, L"V-On Patcher", MB_OK | MB_ICONERROR);
}

int WINAPI wWinMain(HINSTANCE instance, HINSTANCE previous, PWSTR unused, int show)
{
    STARTUPINFOW startup;
    PROCESS_INFORMATION process;
    DWORD length, got, code = 1;
    wchar_t *slash;
    HANDLE errors;

    (void)instance; (void)previous; (void)unused; (void)show;

    length = GetModuleFileNameW(NULL, here, LONG_PATH);
    if (length == 0 || length >= LONG_PATH)
        return fail(L"Cannot tell where this program is.");
    slash = wcsrchr(here, L'\\');
    if (!slash)
        return fail(L"Cannot tell where this program is.");
    *slash = L'\0';

    if (swprintf(python, LONG_PATH, L"%ls\\_internal\\pythonw.exe", here) < 0
        || swprintf(script, LONG_PATH, L"%ls\\_internal\\v-on-patcher.py", here) < 0)
        return fail(L"The path to this program is too long.");
    if (!present(python) || !present(script))
        return fail(L"The _internal folder beside this program is missing or "
                    L"incomplete. Unzip the whole download and run the program "
                    L"from the unzipped folder.");

    if (swprintf(command, LONG_PATH, L"\"%ls\" \"%ls\" %ls",
                 python, script, arguments(GetCommandLineW())) < 0)
        return fail(L"The command line is too long.");

    /* stdin and stdout are passed on as they are, so --version and
       --selfcheck print where this program would have. */
    errors = capture();
    ZeroMemory(&startup, sizeof startup);
    startup.cb = sizeof startup;
    startup.dwFlags = STARTF_USESTDHANDLES;
    startup.hStdInput = GetStdHandle(STD_INPUT_HANDLE);
    startup.hStdOutput = GetStdHandle(STD_OUTPUT_HANDLE);
    startup.hStdError = errors != INVALID_HANDLE_VALUE ? errors : GetStdHandle(STD_ERROR_HANDLE);

    if (!CreateProcessW(python, command, NULL, NULL, TRUE, 0, NULL, NULL,
                        &startup, &process)) {
        if (errors != INVALID_HANDLE_VALUE)
            CloseHandle(errors);
        return fail(L"Python in the _internal folder could not be started.");
    }
    CloseHandle(process.hThread);
    WaitForSingleObject(process.hProcess, INFINITE);
    GetExitCodeProcess(process.hProcess, &code);
    CloseHandle(process.hProcess);

    if (errors != INVALID_HANDLE_VALUE) {
        if (code != 0 && (got = collect(errors)) > 0)
            report(got);
        CloseHandle(errors);
    }
    return (int)code;
}
