#include "text.hpp"
#include "raygui.h"

void Text::draw() {
	GuiLabel(rec, text.c_str());
}