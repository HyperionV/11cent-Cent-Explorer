#ifndef TEXTBOX_HPP_
#define TEXTBOX_HPP_

#include <iostream>
#include <string>

#include "raylib.h"
#include "theme.hpp"
#include "object.hpp"
#include "box.hpp"

class Textbox : public Box {
protected:
	std::string text;
	Color textColor = theme::text;

	void drawText();

public:
	Textbox(Rectangle rec, const std::string &text);
	Textbox(Rectangle rec, const std::string &text, Color color, Color textColor);
	
	Textbox(Rectangle rec, const char* text);
	Textbox(Rectangle rec, const char* text, Color color, Color textColor);

	void draw();
};

#endif // TEXTBOX_HPP_