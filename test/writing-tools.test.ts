import { describe, it } from "mocha"
import should from "should"
import { parseAssistantMessageV3 } from "@core/assistant-message"

const msg = `Intro<function_calls><invoke name="Write"><parameter name="file_path">foo.txt</parameter><parameter name="content">hello world</parameter></invoke><invoke name="MultiEdit"><parameter name="file_path">foo.txt</parameter><parameter name="edits">--- SEARCH\nfoo\n=======\nbar\n+++++++ REPLACE</parameter></invoke><invoke name="PlanModeRespond"><parameter name="response">Sounds good</parameter></invoke></function_calls>End`

describe("parseAssistantMessageV3", () => {
    it("parses Write, MultiEdit, and PlanModeRespond", () => {
        const blocks = parseAssistantMessageV3(msg)
        blocks.length.should.equal(5)
        blocks[1].should.have.properties({ type: "tool_use", name: "write_to_file" })
        ;(blocks[1] as any).params.path.should.equal("foo.txt")
        ;(blocks[1] as any).params.content.should.equal("hello world")
        blocks[2].should.have.properties({ type: "tool_use", name: "replace_in_file" })
        ;(blocks[2] as any).params.path.should.equal("foo.txt")
        ;(blocks[2] as any).params.diff.should.match(/SEARCH/)
        blocks[3].should.have.properties({ type: "tool_use", name: "plan_mode_respond" })
        ;(blocks[3] as any).params.response.should.equal("Sounds good")
    })
})
