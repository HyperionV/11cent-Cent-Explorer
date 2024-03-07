#include "textbox.hpp"
#include "raygui.h"

Textbox::Textbox(Rectangle rec, const std::string &text) : Box(rec), text(text) {}
Textbox::Textbox(Rectangle rec, const std::string &text, Color color, Color textColor) : Box(rec, color), text(text), textColor(textColor) {}

Textbox::Textbox(Rectangle rec, const char* text) : Box(rec), text(text) {}
Textbox::Textbox(Rectangle rec, const char* text, Color color, Color textColor) : Box(rec, color), text(text), textColor(textColor) {}

void Textbox::drawText() {
	int fontSize = 0;
	Vector2 textSize = MeasureTextEx(GetFontDefault(), text.c_str(), fontSize, 2);
	do {
		++fontSize;
		textSize = MeasureTextEx(GetFontDefault(), text.c_str(), fontSize, 2);
	} while(textSize.x < rec.width - 40 && textSize.y < rec.height - 20);

	textSize = MeasureTextEx(GetFontDefault(), text.c_str(), fontSize, 2);

	Vector2 textPos = { rec.x + (rec.width - textSize.x) / 2, rec.y + (rec.height - textSize.y) / 2 };
	DrawTextEx(GetFontDefault(), text.c_str(), textPos, fontSize, 2, textColor);
}

void Textbox::draw() {
	DrawRectangleRec(rec, color);
	drawText();
}