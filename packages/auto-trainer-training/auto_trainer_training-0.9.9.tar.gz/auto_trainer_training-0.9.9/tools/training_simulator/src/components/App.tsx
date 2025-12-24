import {AppShell, Group, SimpleGrid, Text} from "@mantine/core";

import {useTrainingProtocol} from "../hooks/useTrainingProtocol.ts";
import {Protocol} from "./Protocol.tsx";
import {Phase} from "./Phase.tsx";
import {PhaseProgress} from "./PhaseProgress.tsx";
import {ProtocolProgress} from "./ProtocolProgress.tsx";

export const App = () => {
    const protocol = useTrainingProtocol();

    return (
        <AppShell padding="md" header={{height: 44}}>
            <AppShell.Header bg="rgb(43, 43, 43)">
                <Group p={8} align="center">
                    <Text c="white" size="lg" fw={500}>Training Protocol Simulator</Text>
                </Group>
            </AppShell.Header>
            <AppShell.Main>
                <SimpleGrid cols={2} maw={1000}>
                    <ProtocolProgress protocol={protocol}/>
                    <PhaseProgress phase={protocol.phases[5]}/>
                    <Protocol protocol={protocol}/>
                    <Phase phase={protocol.phases[5]}/>
                </SimpleGrid>
            </AppShell.Main>
            <AppShell.Footer>
                <Group p={8} bg="rgb(43, 43, 43)">
                    <Text size="xs" c="white">Mouse-GYM</Text>
                </Group>
            </AppShell.Footer>
        </AppShell>
    )
}
