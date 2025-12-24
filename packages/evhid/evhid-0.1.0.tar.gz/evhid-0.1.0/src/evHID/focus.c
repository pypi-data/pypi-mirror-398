#include <stdio.h>
#include <unistd.h>

int main() {
    // Enable focus tracking
    printf("\x1b[1004h");
    fflush(stdout);

    char buf[10];
    while (read(STDIN_FILENO, buf, sizeof(buf) - 1) > 0) {
        buf[9] = '\0'; // Null-terminate just in case

        if (buf[0] == '\x1b') {
            if (buf[1] == '[' && buf[2] == 'I') {
                printf("Focus gained\n");
            } else if (buf[1] == '[' && buf[2] == 'O') {
                printf("Focus lost\n");
            }
        }
    }

    // Disable focus tracking when done
    printf("\x1b[1004l");
    fflush(stdout);

    return 0;
}
