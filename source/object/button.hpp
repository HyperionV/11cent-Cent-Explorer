#ifndef BUTTON_HPP_
#define BUTTON_HPP_

#include <iostream>
#include <string>

#include "raylib.h"
#include "object.hpp"

class Button : public Object {
private:
	bool state;

public:
	using Object::Object;

	void draw();
	bool clicked();
};

#endif // BUTTON_HPP_