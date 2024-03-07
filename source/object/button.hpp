#ifndef BUTTON_HPP_
#define BUTTON_HPP_

#include <iostream>
#include <string>

#include "raylib.h"
#include "theme.hpp"

#include "object.hpp"
#include "textbox.hpp"

class Button : public Textbox {
private:
	bool state;
	Color focus = theme::focus;

public:
	using Textbox::Textbox;

	void draw();
	bool clicked();
	bool focused();
};

#endif // BUTTON_HPP_