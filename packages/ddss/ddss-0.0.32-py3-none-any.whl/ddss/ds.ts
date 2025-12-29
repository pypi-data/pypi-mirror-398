import { Op, type Sequelize } from "sequelize";
import { Search } from "atsds";
import type { Rule } from "atsds";
import { Fact, Idea, initializeDatabase, insertOrIgnore } from "./orm.ts";
import { strRuleGetStrIdea } from "./utility.ts";

export async function main(addr: string, sequelize?: Sequelize) {
    if (!sequelize) {
        sequelize = await initializeDatabase(addr);
    }

    const search = new Search();
    let maxFact = -1;

    while (true) {
        const begin = Date.now();
        let count = 0;

        const newFacts = await Fact.findAll({
            where: { id: { [Op.gt]: maxFact } },
        });

        for (const fact of newFacts) {
            maxFact = Math.max(maxFact, fact.id);
            search.add(fact.data);
        }

        const tasks: Promise<void>[] = [];

        const handler = (rule: Rule) => {
            const dsStr = rule.toString();
            tasks.push(insertOrIgnore(Fact, dsStr));
            const idea = strRuleGetStrIdea(dsStr);
            if (idea) {
                tasks.push(insertOrIgnore(Idea, idea));
            }
            return false;
        };

        count = search.execute(handler);
        await Promise.all(tasks);

        const end = Date.now();
        const duration = (end - begin) / 1000;
        if (count === 0) {
            const delay = Math.max(0, 0.1 - duration);
            await new Promise((resolve) => setTimeout(resolve, delay * 1000));
        }
    }
}
