"""
Basic usage examples for mpl-richtext showcasing various features.
"""

import matplotlib.pyplot as plt
from mpl_richtext import richtext

def create_example():
    # Set up a clean figure
    fig = plt.figure(figsize=(15, 12), facecolor='white')
    fig.suptitle('mpl-richtext Feature Showcase', fontsize=24, fontweight='bold', y=0.95)
    
    # 1. Colors & Gradients
    ax1 = fig.add_subplot(3, 3, 1)
    ax1.axis('off')
    ax1.set_title('1. Multi-Color Text', loc='left', fontsize=14, fontweight='bold', pad=10)
    
    richtext(0.5, 0.6,
             strings=["Red", "Blue", "Green", "Purple"],
             colors=["#E74C3C", "#3498DB", "#2ECC71", "#9B59B6"],
             fontsize=24, fontweight='bold',
             ha='center', va='center', ax=ax1)
             
    richtext(0.5, 0.3,
             strings=list("RAINBOW"),
             colors=["red", "orange", "gold", "green", "blue", "indigo", "violet"],
             fontsize=18, fontweight='bold',
             ha='center', va='center', ax=ax1)

    # 2. Font Styles & Weights
    ax2 = fig.add_subplot(3, 3, 2)
    ax2.axis('off')
    ax2.set_title('2. Fonts & Styles', loc='left', fontsize=14, fontweight='bold', pad=10)
    
    richtext(0.5, 0.7,
             strings=["Bold", "Italic", "Light"],
             colors=["black"]*3,
             fontweights=["bold", "normal", "light"],
             fontstyles=["normal", "italic", "normal"],
             fontsize=20, ha='center', ax=ax2)
             
    richtext(0.5, 0.4,
             strings=["Serif", "Sans", "Mono"],
             colors=["#34495E"]*3,
             fontfamilies=["serif", "sans-serif", "monospace"],
             fontsize=18, ha='center', ax=ax2)

    # 3. Decorations (Underline & Background)
    ax3 = fig.add_subplot(3, 3, 3)
    ax3.axis('off')
    ax3.set_title('3. Decorations', loc='left', fontsize=14, fontweight='bold', pad=10)
    
    richtext(0.5, 0.7,
             strings=["Underlined", "Text"],
             colors=["#2C3E50", "#E67E22"],
             underlines=[True, True],
             fontsize=20, ha='center', ax=ax3)
             
    richtext(0.5, 0.3,
             strings=[" Highlighted ", " Box "],
             colors=["white", "black"],
             backgroundcolors=["#E74C3C", "#F1C40F"],
             fontsize=18, ha='center', ax=ax3)

    # 4. Sizing & Spacing
    ax4 = fig.add_subplot(3, 3, 4)
    ax4.axis('off')
    ax4.set_title('4. Sizes & Spacing', loc='left', fontsize=14, fontweight='bold', pad=10)
    
    richtext(0.5, 0.5,
             strings=["Small", "Medium", "Large"],
             colors=["#7F8C8D", "#34495E", "#2C3E50"],
             fontsizes=[12, 20, 32],
             ha='center', va='center', ax=ax4)

    # 5. Syntax Highlighting (Code)
    ax5 = fig.add_subplot(3, 3, 5)
    ax5.axis('off')
    ax5.set_title('5. Syntax Highlighting', loc='left', fontsize=14, fontweight='bold', pad=10)
    
    richtext(0.1, 0.6,
             strings=["def ", "hello_world", "():"],
             colors=["#C678DD", "#61AFEF", "#ABB2BF"],
             fontfamily='monospace', fontsize=16, ax=ax5)
             
    richtext(0.1, 0.4,
             strings=["    return ", "'Success!'"],
             colors=["#C678DD", "#98C379"],
             fontfamily='monospace', fontsize=16, ax=ax5)

    # 6. Advanced Alignment
    ax6 = fig.add_subplot(3, 3, 6)
    ax6.axis('off')
    ax6.set_title('6. Alignment', loc='left', fontsize=14, fontweight='bold', pad=10)
    
    richtext(0.5, 0.8, ["Left Aligned"], ["black"], ha='left', fontsize=14, ax=ax6)
    richtext(0.5, 0.5, ["Center Aligned"], ["#E67E22"], ha='center', fontsize=14, ax=ax6)
    richtext(0.5, 0.2, ["Right Aligned"], ["#2980B9"], ha='right', fontsize=14, ax=ax6)
    ax6.axvline(0.5, color='#BDC3C7', linestyle='--', zorder=0)

    # 7. Targeted Overrides (Dictionary)
    ax7 = fig.add_subplot(3, 3, 7)
    ax7.axis('off')
    ax7.set_title('7. Targeted Overrides', loc='left', fontsize=14, fontweight='bold', pad=10)
    
    richtext(0.5, 0.5,
             strings=["Normal", "Red", "Normal", "Blue"], color="green",
             colors={1: "red", 3: "blue"}, fontsizes={1: 20, 3: 30}, fontsize=15,  # Target specific indices
             fontweights={1: "bold", 3: "bold"},
             ha='center', va='center', ax=ax7)

    # 8. Rotated Text
    ax8 = fig.add_subplot(3, 3, 8)
    ax8.axis('off')
    ax8.set_title('8. Rotated Text', loc='left', fontsize=14, fontweight='bold', pad=10)
    
    richtext(0.5, 0.5,
             strings=["Rotated ", "Text"],
             colors=["#8E44AD", "#2C3E50"],
             rotation=45,
             fontsize=24, ha='center', va='center', ax=ax8)

    # 9. Transparency (Alpha)
    ax9 = fig.add_subplot(3, 3, 9)
    ax9.axis('off')
    ax9.set_title('9. Transparency', loc='left', fontsize=14, fontweight='bold', pad=10)
    
    richtext(0.5, 0.5,
             strings=["Solid", "Fade", "Ghost"],
             colors=["#2C3E50"]*3,
             alphas=[1.0, 0.6, 0.2],
             fontsize=24, fontweight='bold',
             ha='center', va='center', ax=ax9)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig('examples/mpl_richtext_examples.png', dpi=200, bbox_inches='tight')
    print("Example image saved.")

if __name__ == "__main__":
    create_example()