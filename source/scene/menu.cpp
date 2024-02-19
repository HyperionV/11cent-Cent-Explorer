#include "raygui.h"
#include "menu.hpp"

Menu::Menu() {
	obj["start"] = new Button((Rectangle){ 540, 500, 200, 50 }, "Start");
	obj["title"] = new Textbox((Rectangle){ 340, 200, 600, 150 }, "Cent Explorer", theme::background, Color({ 255, 255, 255, 255 }));
}

Scene* Menu::update() {
	if(((Button*)(obj["start"]))->clicked())
		std::cout << "Start button clicked" << std::endl;
	return this;
}

void Menu::draw() {
	for(auto& object : obj) object.second->draw();
}

Menu::~Menu() {
	for(auto& object : obj) delete object.second;
}