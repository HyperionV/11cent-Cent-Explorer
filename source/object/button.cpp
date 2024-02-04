#include "raygui.h"
#include "button.hpp"

void Button::draw() {
	state = GuiButton(rec, text.c_str());
}

bool Button::clicked() {
	return state;
}