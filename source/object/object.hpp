#ifndef OBJECT_HPP_
#define OBJECT_HPP_

#include <iostream>
#include <string>

#include "raylib.h"

class Object {
protected:
	Rectangle rec;
	std::string text;

public:
	Object();
	Object(Rectangle rec, const char* text);
	Object(Rectangle rec, const std::string &text);

	virtual void draw() = 0;
};

#endif // OBJECT_HPP_