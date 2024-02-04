#include "raygui.h"
#include "button.hpp"

Button::Button(Rectangle rec, const char* text, bool border) : rec(rec), text(text), border(border), state(false) {}
Button::Button(Rectangle rec, const std::string &text, bool border) : rec(rec), text(text), border(border), state(false) {}

void Button::draw() {
	if (border) state = GuiButton(rec, text.c_str());
	else state = GuiLabelButton(rec, text.c_str());
}

bool Button::clicked() {
	return state;
}