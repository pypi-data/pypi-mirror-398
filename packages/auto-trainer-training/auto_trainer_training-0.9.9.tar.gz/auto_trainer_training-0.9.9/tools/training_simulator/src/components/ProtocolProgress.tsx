import {Card, Group, Stack, Table, Text} from "@mantine/core";

import type {TrainingProtocol} from "../models/trainingProtocol.ts";

export const ProtocolProgress = ({protocol}: { protocol: TrainingProtocol }) => {
    return (
        <Card mih={240} withBorder>
            <Card.Section bg="blue.2">
                <Group p={4} justify="space-between">
                    <Text fw={500}>Protocol Progress</Text>
                </Group>
            </Card.Section>
            {protocol ? <ProtocolProgressContent protocol={protocol}/> : null}
        </Card>
    );
}

const ProtocolProgressContent = ({protocol}: { protocol: TrainingProtocol }) => {
    return (
        <Stack mt={12}>
            <Group justify="stretch" align="start">
                <Stack style={{flexGrow: 1}}>
                    <Table variant="vertical" withTableBorder={true}>
                        <Table.Tbody fz={12}>
                            <Table.Tr>
                                <Table.Th>Started</Table.Th>
                                <Table.Td colSpan={2}>10/17/25 10:42 AM</Table.Td>
                            </Table.Tr>
                            <Table.Tr>
                                <Table.Th>Time in Training</Table.Th>
                                <Table.Td>3.1</Table.Td>
                                <Table.Td bg="blue.0">hr</Table.Td>
                            </Table.Tr>
                            <Table.Tr>
                                <Table.Th>Sessions</Table.Th>
                                <Table.Td colSpan={2}>14</Table.Td>
                            </Table.Tr>
                        </Table.Tbody>
                    </Table>
                </Stack>
                <Stack>
                    <Table variant="vertical" withTableBorder={true}>
                        <Table.Tbody fz={12}>
                            <Table.Tr>
                                <Table.Th>Pellets Presented</Table.Th>
                                <Table.Td>22</Table.Td>
                            </Table.Tr>
                            <Table.Tr>
                                <Table.Th>Pellets Consumed</Table.Th>
                                <Table.Td>15</Table.Td>
                            </Table.Tr>
                            <Table.Tr>
                                <Table.Th>Reaches</Table.Th>
                                <Table.Td>14</Table.Td>
                            </Table.Tr>
                        </Table.Tbody>
                    </Table>
                </Stack>
            </Group>
        </Stack>
    );
}
