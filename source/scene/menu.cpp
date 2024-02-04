#include "raygui.h"
#include "menu.hpp"

Menu::Menu() {
	obj["start"] = new Button((Rectangle){ 540, 500, 200, 50 }, "Start");
	obj["title"] = new Text((Rectangle){ 540, 200, 200, 50 }, "Title");
}

Scene* Menu::update() {
	if(static_cast<Button*>(obj["start"])->clicked())
		std::cout << "Start button clicked" << std::endl;
	return this;
}

void Menu::draw() {
	for(auto& object : obj) object.second->draw();
}