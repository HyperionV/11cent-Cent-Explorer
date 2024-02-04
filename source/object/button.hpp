#ifndef BUTTON_HPP_
#define BUTTON_HPP_

#include <iostream>
#include <string>

#include "raylib.h"

class Button {
private:
	Rectangle rec;
	std::string text;

	bool border;
	bool state;

public:
	Button(Rectangle rec, const char* text, bool border = true);
	Button(Rectangle rec, const std::string &text, bool border = true);

	void draw();
	bool clicked();
};

#endif // BUTTON_HPP_