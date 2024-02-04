#ifndef MENU_HPP_
#define MENU_HPP_

#include <iostream>
#include <string>

#include "raylib.h"
#include "scene.hpp"
#include "button.hpp"

class Menu : public Scene {
private:
	Button playButton;

public:
	Menu();

	Scene* update() override;
	void draw() override;
};

#endif // MENU_HPP_