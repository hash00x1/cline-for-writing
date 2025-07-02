import { describe, it } from "mocha"
import should from "should"
import { SYSTEM_PROMPT } from "@core/prompts/system"
import { DEFAULT_BROWSER_SETTINGS } from "@shared/BrowserSettings"

const stubHub = { getServers: () => [] } as any

describe("SYSTEM_PROMPT", () => {
    it("includes plan mode instructions and writing tools", async () => {
        const prompt = await SYSTEM_PROMPT("/tmp", false, stubHub, DEFAULT_BROWSER_SETTINGS)
        prompt.should.match(/plan_mode_respond/)
        prompt.should.match(/write_to_file/)
        prompt.should.match(/replace_in_file/)
        prompt.should.match(/PLAN MODE/)
    })
})
