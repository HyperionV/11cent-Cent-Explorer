#include "raygui.h"
#include "menu.hpp"

Menu::Menu() : playButton((Rectangle){ 100, 100, 100, 50 }, "Play") {}

Scene* Menu::update() {
	if(playButton.clicked()) std::cout << "Play button clicked" << std::endl;
	return this;
}

void Menu::draw() {
	playButton.draw();
}