"""
5x7 Pixel Font for GitHub Contribution Graph

Each character is represented as a 7-row × 5-column grid.
'#' = pixel on (commit), ' ' = pixel off (no commit)
"""

FONT = {
    "A": [
        " ### ",
        "#   #",
        "#   #",
        "#####",
        "#   #",
        "#   #",
        "#   #",
    ],
    "B": [
        "#### ",
        "#   #",
        "#   #",
        "#### ",
        "#   #",
        "#   #",
        "#### ",
    ],
    "C": [
        " ####",
        "#    ",
        "#    ",
        "#    ",
        "#    ",
        "#    ",
        " ####",
    ],
    "D": [
        "#### ",
        "#   #",
        "#   #",
        "#   #",
        "#   #",
        "#   #",
        "#### ",
    ],
    "E": [
        "#####",
        "#    ",
        "#    ",
        "#### ",
        "#    ",
        "#    ",
        "#####",
    ],
    "F": [
        "#####",
        "#    ",
        "#    ",
        "#### ",
        "#    ",
        "#    ",
        "#    ",
    ],
    "G": [
        " ####",
        "#    ",
        "#    ",
        "#  ##",
        "#   #",
        "#   #",
        " ### ",
    ],
    "H": [
        "#   #",
        "#   #",
        "#   #",
        "#####",
        "#   #",
        "#   #",
        "#   #",
    ],
    "I": [
        "#####",
        "  #  ",
        "  #  ",
        "  #  ",
        "  #  ",
        "  #  ",
        "#####",
    ],
    "J": [
        "#####",
        "    #",
        "    #",
        "    #",
        "    #",
        "#   #",
        " ### ",
    ],
    "K": [
        "#   #",
        "#  # ",
        "# #  ",
        "##   ",
        "# #  ",
        "#  # ",
        "#   #",
    ],
    "L": [
        "#    ",
        "#    ",
        "#    ",
        "#    ",
        "#    ",
        "#    ",
        "#####",
    ],
    "M": [
        "#   #",
        "## ##",
        "# # #",
        "#   #",
        "#   #",
        "#   #",
        "#   #",
    ],
    "N": [
        "#   #",
        "##  #",
        "# # #",
        "#  ##",
        "#   #",
        "#   #",
        "#   #",
    ],
    "O": [
        " ### ",
        "#   #",
        "#   #",
        "#   #",
        "#   #",
        "#   #",
        " ### ",
    ],
    "P": [
        "#### ",
        "#   #",
        "#   #",
        "#### ",
        "#    ",
        "#    ",
        "#    ",
    ],
    "Q": [
        " ### ",
        "#   #",
        "#   #",
        "#   #",
        "# # #",
        "#  # ",
        " ## #",
    ],
    "R": [
        "#### ",
        "#   #",
        "#   #",
        "#### ",
        "# #  ",
        "#  # ",
        "#   #",
    ],
    "S": [
        " ####",
        "#    ",
        "#    ",
        " ### ",
        "    #",
        "    #",
        "#### ",
    ],
    "T": [
        "#####",
        "  #  ",
        "  #  ",
        "  #  ",
        "  #  ",
        "  #  ",
        "  #  ",
    ],
    "U": [
        "#   #",
        "#   #",
        "#   #",
        "#   #",
        "#   #",
        "#   #",
        " ### ",
    ],
    "V": [
        "#   #",
        "#   #",
        "#   #",
        "#   #",
        "#   #",
        " # # ",
        "  #  ",
    ],
    "W": [
        "#   #",
        "#   #",
        "#   #",
        "#   #",
        "# # #",
        "## ##",
        "#   #",
    ],
    "X": [
        "#   #",
        "#   #",
        " # # ",
        "  #  ",
        " # # ",
        "#   #",
        "#   #",
    ],
    "Y": [
        "#   #",
        "#   #",
        " # # ",
        "  #  ",
        "  #  ",
        "  #  ",
        "  #  ",
    ],
    "Z": [
        "#####",
        "    #",
        "   # ",
        "  #  ",
        " #   ",
        "#    ",
        "#####",
    ],
    "0": [
        " ### ",
        "#   #",
        "#  ##",
        "# # #",
        "##  #",
        "#   #",
        " ### ",
    ],
    "1": [
        "  #  ",
        " ##  ",
        "  #  ",
        "  #  ",
        "  #  ",
        "  #  ",
        "#####",
    ],
    "2": [
        " ### ",
        "#   #",
        "    #",
        "  ## ",
        " #   ",
        "#    ",
        "#####",
    ],
    "3": [
        " ### ",
        "#   #",
        "    #",
        "  ## ",
        "    #",
        "#   #",
        " ### ",
    ],
    "4": [
        "#   #",
        "#   #",
        "#   #",
        "#####",
        "    #",
        "    #",
        "    #",
    ],
    "5": [
        "#####",
        "#    ",
        "#    ",
        "#### ",
        "    #",
        "    #",
        "#### ",
    ],
    "6": [
        " ### ",
        "#    ",
        "#    ",
        "#### ",
        "#   #",
        "#   #",
        " ### ",
    ],
    "7": [
        "#####",
        "    #",
        "   # ",
        "  #  ",
        "  #  ",
        "  #  ",
        "  #  ",
    ],
    "8": [
        " ### ",
        "#   #",
        "#   #",
        " ### ",
        "#   #",
        "#   #",
        " ### ",
    ],
    "9": [
        " ### ",
        "#   #",
        "#   #",
        " ####",
        "    #",
        "    #",
        " ### ",
    ],
    " ": [
        "     ",
        "     ",
        "     ",
        "     ",
        "     ",
        "     ",
        "     ",
    ],
}

# Character width (5) + spacing (1)
CHAR_WIDTH = 5
CHAR_SPACING = 1
CHAR_HEIGHT = 7


def get_character(char: str) -> list[str]:
    """Get the pixel grid for a character (uppercase)."""
    return FONT.get(char.upper(), FONT[" "])


def word_to_grid(word: str) -> list[list[int]]:
    """
    Convert a word to a 2D grid of intensity values.

    Returns a 7-row grid where each column represents a week.
    Values: 0 = no commit, 1 = commit (can be scaled for intensity later)
    """
    word = word.upper()

    # Calculate total width
    total_width = len(word) * (CHAR_WIDTH + CHAR_SPACING) - CHAR_SPACING

    # Initialize grid (7 rows × total_width columns)
    grid = [[0 for _ in range(total_width)] for _ in range(CHAR_HEIGHT)]

    # Fill in each character
    col_offset = 0
    for char in word:
        char_grid = get_character(char)
        for row in range(CHAR_HEIGHT):
            for col in range(CHAR_WIDTH):
                if char_grid[row][col] == "#":
                    grid[row][col_offset + col] = 1
        col_offset += CHAR_WIDTH + CHAR_SPACING

    return grid


def print_grid(grid: list[list[int]]) -> None:
    """Print a visual representation of the grid."""
    for row in grid:
        print("".join("█" if cell else " " for cell in row))
