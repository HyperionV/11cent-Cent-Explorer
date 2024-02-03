#ifndef MENU_HPP_
#define MENU_HPP_

#include "scene.hpp"

class Menu : public Scene {
private:
	// ...
public:
	Menu();
	~Menu();

	Scene* update() override;
	void draw() override;
};

#endif // MENU_HPP_