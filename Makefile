bold := $(shell tput bold)
byel := $(bold)$(shell tput setaf 11)
end := $(shell tput sgr0)
EXT_DIR=~/.local/share/albert/org.albert.extension.python/modules/

install: wallabag linkding paperless
	@printf "$(byel)========== Installation Done! ==========$(end)\n"


test: wallabag
	@printf "$(byel)========== Starting Albert ==========$(end)\n"
	albert

wallabag:
	@printf "$(byel)========== Installing wallabag ==========$(end)\n"
	cp -r src/wallabag/ $(EXT_DIR)
	@test -s $(EXT_DIR)/wallabag/config.ini || cp config/wallabag/config.ini $(EXT_DIR)/wallabag

linkding:
	@printf "$(byel)========== Installing linkding ==========$(end)\n"
	cp -r src/linkding/ $(EXT_DIR)
	@test -s $(EXT_DIR)/linkding/config.ini || cp config/linkding/config.ini $(EXT_DIR)/linkding

paperless:
	@printf "$(byel)========== Installing paperless ==========$(end)\n"
	cp -r src/paperless/ $(EXT_DIR)
	@test -s $(EXT_DIR)/paperless/config.ini || cp config/paperless/config.ini $(EXT_DIR)/paperless

.PHONY: all wallabag linkding paperless
