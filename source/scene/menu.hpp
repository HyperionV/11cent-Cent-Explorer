#ifndef MENU_HPP_
#define MENU_HPP_

#include <iostream>
#include <string>
#include <map>

#include "raylib.h"
#include "scene.hpp"

#include "box.hpp"
#include "button.hpp"
#include "textbox.hpp"

class Menu : public Scene {
private:
	std::map<std::string, Object*> obj;

public:
	Menu();
	~Menu();

	Scene* update() override;
	void draw() override;
};

#endif // MENU_HPP_