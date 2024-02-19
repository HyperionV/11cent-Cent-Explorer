#include "raygui.h"
#include "button.hpp"

void Button::draw() {
	DrawRectangleRec(rec, focused() ? focus : color);
	Textbox::drawText();
}

bool Button::clicked() {
	if(IsMouseButtonPressed(MOUSE_LEFT_BUTTON) && CheckCollisionPointRec(GetMousePosition(), rec)) {
		state = !state;
		return true;
	}
	return false;
}

bool Button::focused() {
	return CheckCollisionPointRec(GetMousePosition(), rec);
}