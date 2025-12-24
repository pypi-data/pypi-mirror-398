import {Card, Group, Stack, Table, Text,} from "@mantine/core";

import type {TrainingPhase} from "../models/trainingPhase.ts";

export const PhaseProgress = ({phase}: {phase: TrainingPhase}) => {
    return (
        <Card mih={240} withBorder>
            <Card.Section bg="blue.2">
                <Group p={4} justify="space-between">
                    <Text fw={500}>Phase Progress</Text>
                </Group>
            </Card.Section>
            {phase ? <PhaseProgressContent phase={phase}/> : null}
        </Card>
    );
}

const PhaseProgressContent = ({phase}: {phase: TrainingPhase}) => {
    return (
        <Stack mt={12}>
            <Group justify="stretch" align="start">
                <Stack style={{flexGrow: 1}}>
                    <Table variant="vertical" withTableBorder={true}>
                        <Table.Tbody fz={12}>
                            <Table.Tr>
                                <Table.Th>Started</Table.Th>
                                <Table.Td colSpan={2}>10/17/25 11:06 AM</Table.Td>
                            </Table.Tr>
                            <Table.Tr>
                                <Table.Th>Time in Training</Table.Th>
                                <Table.Td>39</Table.Td>
                                <Table.Td bg="blue.0">sec</Table.Td>
                            </Table.Tr>
                            <Table.Tr>
                                <Table.Th>Sessions</Table.Th>
                                <Table.Td colSpan={2}>1</Table.Td>
                            </Table.Tr>
                            <Table.Tr>
                                <Table.Th>Attempts</Table.Th>
                                <Table.Td colSpan={2}>2</Table.Td>
                            </Table.Tr>
                        </Table.Tbody>
                    </Table>
                </Stack>
                <Stack>
                    <Table variant="vertical" withTableBorder={true}>
                        <Table.Tbody fz={12}>
                            <Table.Tr>
                                <Table.Th>Pellets Presented</Table.Th>
                                <Table.Td>3</Table.Td>
                            </Table.Tr>
                            <Table.Tr>
                                <Table.Th>Pellets Consumed</Table.Th>
                                <Table.Td>1</Table.Td>
                            </Table.Tr>
                            <Table.Tr>
                                <Table.Th>Reaches</Table.Th>
                                <Table.Td>0</Table.Td>
                            </Table.Tr>
                        </Table.Tbody>
                    </Table>
                </Stack>
            </Group>
        </Stack>
    );
}
