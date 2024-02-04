#ifndef TEXT_HPP_
#define TEXT_HPP_

#include <iostream>
#include <string>

#include "raylib.h"
#include "object.hpp"

class Text : public Object {
public:
	using Object::Object;
	void draw();
};

#endif // TEXT_HPP_