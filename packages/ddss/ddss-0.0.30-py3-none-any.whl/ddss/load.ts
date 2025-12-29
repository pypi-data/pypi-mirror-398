import * as readline from "node:readline/promises";
import { stdin as input } from "node:process";
import type { Sequelize } from "sequelize";
import { parse } from "atsds-bnf";
import { Fact, Idea, initializeDatabase, insertOrIgnore } from "./orm.ts";
import { strRuleGetStrIdea } from "./utility.ts";

export async function main(addr: string, sequelize?: Sequelize) {
    if (!sequelize) {
        sequelize = await initializeDatabase(addr);
    }

    const rl = readline.createInterface({
        input,
        terminal: false,
    });

    for await (const line of rl) {
        const data = line.trim();
        if (data === "" || data.startsWith("//")) {
            continue;
        }

        try {
            const ds = parse(data);
            const dsStr = ds.toString();

            await insertOrIgnore(Fact, dsStr);
            const idea = strRuleGetStrIdea(dsStr);
            if (idea) {
                await insertOrIgnore(Idea, idea);
            }
        } catch (e) {
            console.error(`error: ${e}`);
        }
    }
    rl.close();
}
